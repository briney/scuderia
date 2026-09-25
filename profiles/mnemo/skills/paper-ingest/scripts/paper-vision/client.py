"""Independent pinned inspection client. No host routing, config, or fallback APIs."""
import base64
from datetime import datetime, timezone
import hashlib
import http.client
import io
import json
import os
from pathlib import Path
import stat
from typing import Any
from urllib.parse import urlsplit

MAX_IMAGES = 4
MAX_IMAGE_BYTES = 20 * 1024 * 1024
MAX_DIMENSION = 12000
MAX_PIXELS = 40_000_000
MAX_QUESTION = 8000
MAX_LABEL = 120
MAX_PATH = 4096
MAX_RESPONSE_BYTES = 2 * 1024 * 1024
MAX_FINDINGS = 100_000
MAX_INPUT_BYTES = 65536
LIMITATIONS = ('These are model observations, not human acceptance or an independent second-model verdict. '
               'Unreadable details and crop-only context limit conclusions; overall completeness is not established. '
               'The server-reported model identity is checked, but server internals are not independently attested.')
ROOT = Path(__file__).resolve().parent


class InspectionError(Exception):
    """Only fixed, non-secret error codes may be used here."""


def require(condition, code):
    if not condition:
        raise InspectionError(code)


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def encoded(value):
    return json.dumps(value, ensure_ascii=True, allow_nan=False, sort_keys=True,
                      separators=(',', ':')).encode('utf-8')


def timestamp():
    return datetime.now(timezone.utc).isoformat()


def put(path, raw):
    """Exclusive, flushed evidence files, never symlinks or overwritten files."""
    with path.open('xb') as stream:
        stream.write(raw)
        stream.flush()
        os.fsync(stream.fileno())
    fd = os.open(path.parent, os.O_RDONLY)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def text_ok(value, limit):
    return (isinstance(value, str) and 0 < len(value) <= limit and bool(value.strip())
            and '\x00' not in value and not any(0xD800 <= ord(c) <= 0xDFFF for c in value))


def local_path(value):
    require(text_ok(value, MAX_PATH) and '://' not in value, 'invalid-path')
    return Path(value).expanduser().absolute()


def validate_args(args):
    require(isinstance(args, dict) and set(args) == {'images', 'question', 'output_dir'}, 'invalid-arguments')
    require(text_ok(args['question'], MAX_QUESTION), 'invalid-question')
    images = args['images']
    require(isinstance(images, list) and 1 <= len(images) <= MAX_IMAGES, 'invalid-images')
    local_path(args['output_dir'])
    for image in images:
        require(isinstance(image, dict) and set(image) == {'path', 'label'}, 'invalid-image-entry')
        local_path(image['path'])
        require(text_ok(image['label'], MAX_LABEL), 'invalid-label')


def read_image(value):
    path = local_path(value)
    try:
        fd = os.open(path, os.O_RDONLY | os.O_NONBLOCK | os.O_NOFOLLOW)
        with os.fdopen(fd, 'rb') as stream:
            info = os.fstat(stream.fileno())
            require(stat.S_ISREG(info.st_mode), 'image-unavailable')
            require(info.st_size <= MAX_IMAGE_BYTES, 'image-too-large')
            raw = stream.read(MAX_IMAGE_BYTES + 1)
    except OSError:
        raise InspectionError('image-unavailable') from None
    require(len(raw) <= MAX_IMAGE_BYTES, 'image-too-large')
    try:
        # Delayed import: registering the tool neither reads credentials nor installs packages.
        from PIL import Image
    except ImportError:
        raise InspectionError('missing-pillow') from None
    try:
        with Image.open(io.BytesIO(raw)) as image:
            fmt, dimensions = image.format, image.size
            require(fmt in ('PNG', 'JPEG'), 'unsupported-image-type')
            w, h = dimensions
            require(0 < w <= MAX_DIMENSION and 0 < h <= MAX_DIMENSION and w * h <= MAX_PIXELS,
                    'image-dimensions')
            require(getattr(image, 'n_frames', 1) == 1, 'animated-image')
            image.verify()
        # Verify structure AND fully decode to reject truncated compressed streams.
        with Image.open(io.BytesIO(raw)) as image:
            image.load()
    except InspectionError:
        raise
    except Exception:
        raise InspectionError('invalid-image') from None
    mime = 'image/png' if fmt == 'PNG' else 'image/jpeg'
    return raw, {'path': str(path), 'sha256': digest(raw), 'mime_type': mime,
                 'dimensions': list(dimensions), 'bytes': len(raw)}


def build_wire(record, image_bytes):
    """Deterministic reconstruction from input.json and exact evidence copies."""
    content = [{'type': 'text', 'text': record['question']}]
    for image, raw in zip(record['images'], image_bytes):
        content.append({'type': 'text', 'text': image['label']})
        content.append({'type': 'image_url', 'image_url': {
            'url': 'data:' + image['mime_type'] + ';base64,' + base64.b64encode(raw).decode('ascii')}})
    return encoded({**record['recipe']['settings'], 'messages': [
        {'role': 'system', 'content': record['prompt']}, {'role': 'user', 'content': content}]})


def post(wire, key, recipe):
    """One direct stdlib connection and one POST. No redirects, proxies, or retry loop."""
    endpoint = urlsplit(recipe['endpoint'])
    conn = http.client.HTTPConnection(endpoint.hostname, endpoint.port, timeout=recipe['timeout_seconds'])
    try:
        conn.request('POST', endpoint.path, body=wire,
                     headers={'Content-Type': 'application/json', 'Authorization': 'Bearer ' + key})
        response = conn.getresponse()
        try:
            return response.status, response.read(MAX_RESPONSE_BYTES + 1)
        finally:
            response.close()
    except TimeoutError:
        raise InspectionError('timeout') from None
    except (OSError, http.client.HTTPException):
        raise InspectionError('http-failure') from None
    finally:
        conn.close()


def scrub(value: Any, key: str) -> Any:
    """Sanitize decoded JSON strings and keys, including escaped credential echoes."""
    if isinstance(value, str):
        return value.replace(key, '[REDACTED]') if key else value
    if isinstance(value, list):
        return [scrub(v, key) for v in value]
    if isinstance(value, dict):
        return {scrub(k, key): scrub(v, key) for k, v in value.items()}
    return value


def parse_json(raw):
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise ValueError()
            result[key] = value
        return result
    def constant(value):
        raise ValueError()
    return json.loads(raw, object_pairs_hook=pairs, parse_constant=constant)


def retain_response(out, raw, key, result):
    result['response_sha256'] = digest(raw)
    if len(raw) > MAX_RESPONSE_BYTES:
        result['response_sha256_scope'] = 'bounded prefix, not complete response'
        safe = b'[Response exceeded byte limit; body omitted to avoid partial credential disclosure.]\n'
        error = 'response-too-large'
        env = None
    else:
        result['response_sha256_scope'] = 'complete response body'
        try:
            env = parse_json(raw)
            safe = encoded(scrub(env, key))
            error = None
        except (ValueError, UnicodeError, RecursionError):
            env = None
            safe = b'[Non-JSON or invalid JSON response omitted; unsafe body is not retained.]\n'
            error = 'invalid-response'
    result['response_sanitized'] = safe != raw
    result['sanitized_response_sha256'] = digest(safe)
    put(out / 'response.sanitized.txt', safe)
    return env, error


def findings(env, result):
    require(isinstance(env, dict), 'invalid-response')
    result['returned_model'] = env.get('model')
    result['usage'] = env.get('usage')
    choices = env.get('choices')
    if isinstance(choices, list) and len(choices) == 1 and isinstance(choices[0], dict):
        result['finish_reason'] = choices[0].get('finish_reason')
    require('error' not in env, 'server-error')
    require(env.get('model') == result['settings']['model'], 'wrong-model')
    require(isinstance(choices, list) and len(choices) == 1 and isinstance(choices[0], dict), 'invalid-response')
    choice = choices[0]
    require(choice.get('finish_reason') == 'stop', 'non-stop-finish')
    message = choice.get('message')
    require(isinstance(message, dict) and not message.get('tool_calls') and not message.get('function_call'),
            'invalid-response')
    text = message.get('content')
    if not isinstance(text, str) or not text.strip():
        raise InspectionError('empty-findings')
    require(len(text) <= MAX_FINDINGS, 'findings-too-large')
    return text


def inspect(args):
    """Reserve a new evidence directory even for failed valid-shape requests."""
    out = None
    key = ''
    result = {'status': 'error', 'attempted': False, 'timestamp': timestamp(),
              'returned_model': None, 'finish_reason': None, 'usage': None, 'findings': None,
              'limitations': LIMITATIONS}
    try:
        # Read exactly this credential at invocation, never any host configuration.
        key = os.environ.get('LITELLM_API_KEY', '')
        require(isinstance(args, dict), 'invalid-arguments')
        # Reject secrets in caller-controlled metadata rather than persisting them.
        require(not key or key not in json.dumps(args, ensure_ascii=False), 'credential-in-input')
        candidate = local_path(args.get('output_dir'))
        require(not any(p.is_symlink() for p in (candidate, *candidate.parents)), 'unsafe-output')
        try:
            candidate.mkdir(mode=0o700)
        except FileExistsError:
            raise InspectionError('output-exists') from None
        except OSError:
            raise InspectionError('output-unavailable') from None
        out = candidate
        result['output_dir'] = str(out)
        put(out / 'attempt.json', encoded({**result, 'status': 'reserved',
                                         'note': 'Never reuse this directory, including after interruption.'}))
        validate_args(args)
        recipe_raw = (ROOT / 'recipe.json').read_bytes()
        recipe = json.loads(recipe_raw)
        prompt_raw = (ROOT / 'prompt.txt').read_bytes()
        put(out / 'recipe.json', recipe_raw)
        result.update(recipe_sha256=digest(recipe_raw), prompt_sha256=digest(prompt_raw),
                      provider_identity=recipe['provider_identity'], settings=recipe['settings'],
                      endpoint=recipe['endpoint'], credential_env=recipe['credential_env'],
                      timeout_seconds=recipe['timeout_seconds'], retries=0, redirects=False, proxies=False)
        record = {'question': args['question'], 'images': [], 'recipe': recipe,
                  'prompt': prompt_raw.decode('utf-8'), 'wire_encoding': 'sorted compact ASCII JSON, UTF-8 bytes'}
        # Metadata for early failures; input.json is the complete reconstructable record.
        put(out / 'submitted.json', encoded(args))
        require(bool(key.strip()), 'missing-credential')
        require(key.isascii() and not any(ord(c) < 33 or ord(c) == 127 for c in key), 'invalid-credential')
        raws = []
        for n, image in enumerate(args['images'], 1):
            raw, row = read_image(image['path'])
            require(key.encode() not in raw, 'credential-in-image')
            row.update(label=image['label'], evidence_file=f'image-{n:02d}.' + ('png' if row['mime_type'] == 'image/png' else 'jpg'))
            put(out / row['evidence_file'], raw)
            record['images'].append(row)
            raws.append(raw)
        put(out / 'input.json', encoded(record))
        wire = build_wire(record, raws)
        result.update(request_sha256=digest(wire), request_bytes=len(wire), images=record['images'])
        # Durable marker precedes network activity. A crash makes delivery unknown, not retryable.
        put(out / 'post-reserved.json', encoded({**result, 'status': 'post-reserved', 'attempted': True}))
        result['attempted'] = True
        status, raw = post(wire, key, recipe)
        result['http_status'] = status
        env, response_error = retain_response(out, raw, key, result)
        require(status == 200, 'http-status')
        require(response_error is None, response_error)
        result['findings'] = findings(env, result)
        result['status'] = 'ok'
    except InspectionError as exc:
        result['error'] = exc.args[0]
    except Exception:
        # Never format arbitrary exceptions: they can contain auth headers or server data.
        result['error'] = 'internal-error'
    result['completed_at'] = timestamp()
    result = scrub(result, key)
    if out is not None:
        try:
            put(out / 'result.json', encoded(result))
        except Exception:
            result['status'] = 'error'
            result['error'] = 'evidence-write-failed'
    return result


def paper_vision_inspect(args, **kwargs):
    """Hermes-compatible JSON-string handler; host kwargs cannot alter routing."""
    try:
        return encoded(inspect(args)).decode('utf-8')
    except Exception:
        return '{"status":"error","error":"internal-error"}'
