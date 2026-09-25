"""Offline tests only. Every model response below is SYNTHETIC, not inference."""
import base64
import contextlib
import copy
import hashlib
import http.client
import importlib.util
import io
import json
import os
from pathlib import Path
import socket
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from PIL import Image

# Deploy an isolated copy with a synthetic route, never the instance's recipe.
import shutil
_RUNTIME = Path(__file__).resolve().parents[2]/'paper-vision'
_DEPLOYMENT = tempfile.TemporaryDirectory(prefix='paper-vision-deployment-')
ROOT = Path(_DEPLOYMENT.name).resolve()
for _name in ('client.py', 'cli.py', '__init__.py', 'plugin.yaml', 'prompt.txt'):
    shutil.copy2(_RUNTIME/_name, ROOT/_name)
shutil.copy2(Path(__file__).parent/'recipe.json', ROOT/'recipe.json')
os.environ['PAPER_VISION_TEST_SCRATCH'] = os.environ.get('TMPDIR', str(ROOT))
sys.path.insert(0, str(ROOT))
import client
import cli

SYNTHETIC_KEY = 'SYNTHETIC-credential-never-valid-42'
SYNTHETIC_RESPONSE = {
    'model': 'qwen3.8-27b', 'choices': [{'finish_reason': 'stop', 'message': {
        'content': 'SYNTHETIC observations: crop matches source. Limitations: tiny labels unreadable.'}}],
    'usage': {'prompt_tokens': 12, 'completion_tokens': 18},
}


class Response(io.BytesIO):
    status = 200


class FakeConnection:
    calls = []
    response = json.dumps(SYNTHETIC_RESPONSE).encode()
    status = 200
    error: Exception | None = None
    interrupted = False
    closed = 0

    def __init__(self, host, port=None, timeout=None):
        self.host, self.port, self.timeout = host, port, timeout

    def request(self, method, path, body=None, headers=None):
        self.calls.append((self.host, self.port, self.timeout, method, path, body, headers))
        if self.interrupted:
            raise KeyboardInterrupt()
        if self.error:
            raise self.error

    def getresponse(self):
        r = Response(self.response)
        r.status = self.status
        return r

    def close(self):
        type(self).closed += 1


def deny_socket(*args, **kwargs):
    raise AssertionError('OFFLINE: sockets forbidden')


class InspectionTests(unittest.TestCase):
    def setUp(self):
        scratch = Path(os.environ['PAPER_VISION_TEST_SCRATCH']).resolve()
        self.temp = tempfile.TemporaryDirectory(prefix='paper-vision-test-', dir=scratch)
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.page = self.root / 'page.png'
        self.crop = self.root / 'crop.jpg'
        Image.new('RGB', (20, 30), 'white').save(self.page)
        Image.new('RGB', (10, 12), 'blue').save(self.crop)
        self.args = {'images': [{'path': str(self.page), 'label': 'original page'},
                                {'path': str(self.crop), 'label': 'candidate crop'}],
                     'question': 'Compare source and crop; disclose unreadable details.',
                     'output_dir': str(self.root / 'evidence')}
        self.env = patch.dict(os.environ, {'LITELLM_API_KEY': SYNTHETIC_KEY})
        self.env.start()
        self.addCleanup(self.env.stop)
        self.sock = patch.object(socket, 'socket', deny_socket)
        self.sock.start()
        self.addCleanup(self.sock.stop)
        self.conn = patch.object(http.client, 'HTTPConnection', FakeConnection)
        self.conn.start()
        self.addCleanup(self.conn.stop)
        FakeConnection.calls = []
        FakeConnection.response = json.dumps(SYNTHETIC_RESPONSE).encode()
        FakeConnection.status = 200
        FakeConnection.error = None
        FakeConnection.interrupted = False
        FakeConnection.closed = 0

    def invoke(self, args=None):
        return json.loads(client.paper_vision_inspect(self.args if args is None else args))

    def assert_error(self, code):
        r = self.invoke()
        self.assertEqual(r['status'], 'error', r)
        self.assertEqual(r['error'], code, r)
        return r

    def test_success_bytes_labels_and_reconstructable_provenance(self):
        r = self.invoke()
        self.assertEqual(r['status'], 'ok', r)
        self.assertIn('SYNTHETIC', r['findings'])
        self.assertIn('not human acceptance', r['limitations'])
        self.assertEqual(len(FakeConnection.calls), 1)
        host, port, timeout, method, path, wire, headers = FakeConnection.calls[0]
        self.assertEqual((host, port, timeout, method, path),
                         ('example.invalid', 4000, 1200, 'POST', '/v1/chat/completions'))
        self.assertEqual(headers['Authorization'], 'Bearer ' + SYNTHETIC_KEY)
        payload = json.loads(wire)
        self.assertEqual(payload['model'], 'qwen3.8-27b')
        self.assertEqual(payload['temperature'], 0)
        self.assertEqual(payload['max_tokens'], 65536)
        self.assertFalse(any('reason' in k for k in payload))
        content = payload['messages'][1]['content']
        self.assertEqual(content[0]['text'], self.args['question'])
        out = Path(self.args['output_dir'])
        record = json.loads((out / 'input.json').read_text())
        self.assertEqual(record['question'], self.args['question'])
        for n, original in enumerate((self.page, self.crop)):
            self.assertEqual(content[1 + n * 2]['text'], self.args['images'][n]['label'])
            encoded = content[2 + n * 2]['image_url']['url']
            self.assertEqual(base64.b64decode(encoded.split(',', 1)[1]), original.read_bytes())
            row = record['images'][n]
            saved = out / row['evidence_file']
            self.assertFalse(saved.is_symlink())
            self.assertEqual(saved.stat().st_nlink, 1)
            self.assertEqual(saved.read_bytes(), original.read_bytes())
            self.assertEqual(row['sha256'], hashlib.sha256(saved.read_bytes()).hexdigest())
        self.assertEqual(record['images'][0]['dimensions'], [20, 30])
        self.assertEqual(record['images'][1]['mime_type'], 'image/jpeg')
        self.assertEqual(r['request_sha256'], hashlib.sha256(wire).hexdigest())
        self.assertEqual(client.build_wire(record, [(out / x['evidence_file']).read_bytes() for x in record['images']]), wire)
        self.assertEqual(r['returned_model'], 'qwen3.8-27b')
        self.assertEqual(r['finish_reason'], 'stop')
        self.assertEqual(r['usage'], SYNTHETIC_RESPONSE['usage'])
        self.assertEqual(r['recipe_sha256'], hashlib.sha256((ROOT / 'recipe.json').read_bytes()).hexdigest())
        self.assertEqual(r['prompt_sha256'], hashlib.sha256((ROOT / 'prompt.txt').read_bytes()).hexdigest())
        self.assertTrue(r['timestamp'])
        self.assertTrue((out / 'post-reserved.json').is_file())
        self.assertFalse((out / 'request-wire.json').exists())
        self.page.write_bytes(b'source changed after inspection')
        self.assertTrue((out / record['images'][0]['evidence_file']).read_bytes().startswith(b'\x89PNG'))

    def test_missing_credentials_retains_failure_without_post(self):
        with patch.dict(os.environ, {}, clear=True):
            r = self.assert_error('missing-credential')
        self.assertFalse(FakeConnection.calls)
        self.assertTrue((Path(self.args['output_dir']) / 'result.json').is_file())
        self.assertFalse(r['attempted'])

    def test_missing_image(self):
        self.page.unlink()
        self.assert_error('image-unavailable')
        self.assertFalse(FakeConnection.calls)

    def test_malformed_image(self):
        self.page.write_bytes(b'not an image')
        self.assert_error('invalid-image')
        self.assertFalse(FakeConnection.calls)

    def test_wrong_actual_type(self):
        Image.new('RGB', (10, 10)).save(self.page, format='GIF')
        self.assert_error('unsupported-image-type')

    def test_truncated_image(self):
        self.page.write_bytes(self.page.read_bytes()[:40])
        self.assert_error('invalid-image')

    def test_image_symlink_and_nonregular(self):
        self.page.unlink()
        self.page.symlink_to(self.crop)
        self.assert_error('image-unavailable')
        self.assertFalse(FakeConnection.calls)

    def test_existing_output_unchanged(self):
        out = Path(self.args['output_dir'])
        out.mkdir()
        (out / 'keep').write_text('untouched')
        self.assert_error('output-exists')
        self.assertEqual(list(out.iterdir()), [out / 'keep'])
        self.assertEqual((out / 'keep').read_text(), 'untouched')
        self.assertFalse(FakeConnection.calls)

    def test_output_symlink(self):
        Path(self.args['output_dir']).symlink_to(self.root, target_is_directory=True)
        self.assert_error('unsafe-output')
        self.assertFalse(FakeConnection.calls)

    def test_input_limits_and_overrides(self):
        mutations = [None, {}, {'images': []}, {'images': self.args['images'] * 3},
                     {'question': ''}, {'question': ' '}, {'question': 'x' * 8001},
                     {'images': [{'path': str(self.page), 'label': 'x' * 121}]},
                     {'images': [{'path': 'https://example.invalid/x.png', 'label': 'x'}]},
                     {'images': [{'path': str(self.page), 'label': 'x', 'mime': 'text/plain'}]}]
        mutations += [{k: 'not-allowed'} for k in ['model', 'provider', 'endpoint', 'credential_env', 'temperature', 'transport']]
        for i, mutation in enumerate(mutations):
            with self.subTest(mutation=mutation):
                args = None if mutation is None else ({} if mutation == {} else {**self.args, **mutation})
                if args:
                    args['output_dir'] = str(self.root / f'invalid-{i}')
                r = json.loads(client.paper_vision_inspect(args))
                self.assertEqual(r['status'], 'error', r)
        self.assertFalse(FakeConnection.calls)

    def test_file_and_pixel_limits(self):
        for name, value, code in [('MAX_IMAGE_BYTES', 8, 'image-too-large'),
                                  ('MAX_DIMENSION', 19, 'image-dimensions'),
                                  ('MAX_PIXELS', 500, 'image-dimensions')]:
            with self.subTest(name=name), patch.object(client, name, value):
                self.args['output_dir'] = str(self.root / name)
                self.assert_error(code)
        self.assertFalse(FakeConnection.calls)

    def test_bad_response_envelopes(self):
        cases = [(dict(model='other'), 'wrong-model'),
                 (dict(choices=[{'finish_reason': 'length', 'message': {'content': 'partial'}}]), 'non-stop-finish'),
                 (dict(choices=[{'finish_reason': 'stop', 'message': {'content': ''}}]), 'empty-findings'),
                 (dict(choices=[{'finish_reason': 'stop', 'message': {'content': '  '}}]), 'empty-findings'),
                 (dict(error={'message': 'SYNTHETIC server error'}), 'server-error'),
                 (dict(choices=[]), 'invalid-response')]
        for i, (change, code) in enumerate(cases):
            with self.subTest(code=code):
                FakeConnection.response = json.dumps({**SYNTHETIC_RESPONSE, **change}).encode()
                self.args['output_dir'] = str(self.root / f'bad-response-{i}')
                self.assert_error(code)
                self.assertTrue((Path(self.args['output_dir']) / 'response.sanitized.txt').exists())
        self.assertEqual(len(FakeConnection.calls), len(cases))

    def test_malformed_json_and_response_byte_limit(self):
        FakeConnection.response = b'bad json'
        self.assert_error('invalid-response')
        self.args['output_dir'] = str(self.root / 'large')
        FakeConnection.response = b'x' * 300
        with patch.object(client, 'MAX_RESPONSE_BYTES', 100):
            self.assert_error('response-too-large')
        self.assertEqual(len(FakeConnection.calls), 2)

    def test_timeout_and_http_failure_are_single_attempts(self):
        for i, error in enumerate([TimeoutError(SYNTHETIC_KEY), OSError(SYNTHETIC_KEY)]):
            with self.subTest(error=type(error).__name__):
                FakeConnection.error = error
                self.args['output_dir'] = str(self.root / f'failure-{i}')
                self.assert_error('timeout' if i == 0 else 'http-failure')
                self.assert_error('output-exists')
        self.assertEqual(len(FakeConnection.calls), 2)
        self.assertEqual(FakeConnection.closed, 2)

    def test_redirects_never_followed_and_proxies_ignored(self):
        with patch.dict(os.environ, {'http_proxy': 'http://evil.invalid', 'HTTP_PROXY': 'http://evil.invalid',
                                     'ALL_PROXY': 'http://evil.invalid'}):
            for status in (301, 302, 303, 307, 308, 401, 500):
                FakeConnection.status = status
                self.args['output_dir'] = str(self.root / f'http-{status}')
                self.assert_error('http-status')
        self.assertEqual(len(FakeConnection.calls), 7)
        self.assertTrue(all(call[0] == 'example.invalid' for call in FakeConnection.calls))

    def test_secret_echo_redaction(self):
        for i, body in enumerate([
            json.dumps({**SYNTHETIC_RESPONSE, 'echo': SYNTHETIC_KEY}).encode(),
            json.dumps({**SYNTHETIC_RESPONSE, 'echo': SYNTHETIC_KEY}).replace('SYNTHETIC-', '\\u0053YNTHETIC-').encode(),
            ('not JSON ' + SYNTHETIC_KEY).encode(),
            json.dumps({**SYNTHETIC_RESPONSE, 'choices': [{'finish_reason': 'stop', 'message': {'content': SYNTHETIC_KEY}}]}).encode(),
        ]):
            self.args['output_dir'] = str(self.root / f'echo-{i}')
            FakeConnection.response = body
            r = self.invoke()
            self.assertNotIn(SYNTHETIC_KEY, json.dumps(r))
            for p in Path(self.args['output_dir']).rglob('*'):
                if p.is_file():
                    self.assertNotIn(SYNTHETIC_KEY.encode(), p.read_bytes(), p.name)
            self.assertTrue(r['response_sanitized'])

    def test_interrupted_reservation_cannot_be_reused(self):
        FakeConnection.interrupted = True
        with self.assertRaises(KeyboardInterrupt):
            self.invoke()
        self.assertTrue((Path(self.args['output_dir']) / 'post-reserved.json').is_file())
        FakeConnection.interrupted = False
        self.assert_error('output-exists')
        self.assertEqual(len(FakeConnection.calls), 1)
        self.assertEqual(FakeConnection.closed, 1)

    def test_auxiliary_and_synthetic_hermes_config_ignored(self):
        home = self.root / 'synthetic-hermes-home'
        home.mkdir()
        config = home / 'config.yaml'
        config.write_text('model:\n  default: SYNTHETIC-not-qwen\n  base_url: http://evil.invalid\n')
        with patch.dict(os.environ, {'HERMES_HOME': str(home), 'AUXILIARY_VISION_MODEL': 'wrong',
                                     'AUXILIARY_VISION_PROVIDER': 'wrong', 'AUXILIARY_VISION_BASE_URL': 'http://evil.invalid'}):
            self.assertEqual(self.invoke()['status'], 'ok')
        self.assertEqual(json.loads(FakeConnection.calls[0][5])['model'], 'qwen3.8-27b')
        self.assertEqual(FakeConnection.calls[0][0], 'example.invalid')
        self.assertEqual(config.read_text(), 'model:\n  default: SYNTHETIC-not-qwen\n  base_url: http://evil.invalid\n')
        # Inspect actual imports rather than searching incidental prose.
        import ast
        tree = ast.parse((ROOT / 'client.py').read_text())
        imports = [n.module or '' for n in ast.walk(tree) if isinstance(n, ast.ImportFrom)]
        imports += [a.name for n in ast.walk(tree) if isinstance(n, ast.Import) for a in n.names]
        self.assertFalse(any(s.startswith(('hermes', 'agent', 'tools', 'plugins')) for s in imports))

    def test_schema_handler_registration_agree(self):
        spec = importlib.util.spec_from_file_location('synthetic_paper_plugin', ROOT / '__init__.py',
                                                     submodule_search_locations=[str(ROOT)])
        module = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = module
        spec.loader.exec_module(module)
        class Context:
            def register_tool(inner, **kwargs):
                inner.kwargs = kwargs
        ctx = Context()
        module.register(ctx)
        kw = ctx.kwargs
        self.assertEqual(kw['name'], 'paper_vision_inspect')
        self.assertFalse(kw.get('override', False))
        schema = kw['schema']['parameters']
        self.assertEqual(set(schema['required']), set(self.args))
        self.assertEqual(set(schema['properties']), set(self.args))
        self.assertFalse(schema['additionalProperties'])
        self.assertEqual(schema['properties']['images']['maxItems'], client.MAX_IMAGES)
        result = json.loads(kw['handler'](self.args, model='ignored', endpoint='ignored', task_id='synthetic'))
        self.assertEqual(result['status'], 'ok', result)
        self.assertEqual(FakeConnection.calls[0][0], 'example.invalid')

    def test_nonregular_input_rejected_without_blocking(self):
        self.page.unlink()
        os.mkfifo(self.page)
        self.assert_error('image-unavailable')
        self.assertFalse(FakeConnection.calls)

    def test_animated_png_rejected(self):
        Image.new('RGB', (10, 10), 'white').save(
            self.page, format='PNG', save_all=True,
            append_images=[Image.new('RGB', (10, 10), 'blue')], duration=100, loop=0)
        self.assert_error('animated-image')
        self.assertFalse(FakeConnection.calls)

    def test_maximum_count_and_text_boundaries(self):
        self.args['images'] *= 2
        for image in self.args['images']:
            image['label'] = 'a' * client.MAX_LABEL
        self.args['question'] = 'q' * client.MAX_QUESTION
        self.assertEqual(self.invoke()['status'], 'ok')
        self.assertEqual(len(FakeConnection.calls), 1)

    def test_secret_echo_in_error_body_and_exception_never_exposed(self):
        for i, status in enumerate((401, 500)):
            self.args['output_dir'] = str(self.root / f'secret-http-{i}')
            FakeConnection.status = status
            FakeConnection.response = json.dumps({'error': {'message': SYNTHETIC_KEY}}).encode()
            r = self.assert_error('http-status')
            self.assertNotIn(SYNTHETIC_KEY, json.dumps(r))
        self.args['output_dir'] = str(self.root / 'unexpected')
        FakeConnection.error = RuntimeError('Authorization: Bearer ' + SYNTHETIC_KEY)
        r = self.assert_error('internal-error')
        self.assertNotIn(SYNTHETIC_KEY, json.dumps(r))
        for p in self.root.rglob('*'):
            if p.is_file() and p.suffix not in ('.png', '.jpg'):
                self.assertNotIn(SYNTHETIC_KEY.encode(), p.read_bytes())

    def test_secret_input_is_not_copied_or_written(self):
        self.args['question'] = SYNTHETIC_KEY
        self.assert_error('credential-in-input')
        self.assertFalse(Path(self.args['output_dir']).exists())
        self.args['question'] = 'Inspect.'
        self.page.write_bytes(self.page.read_bytes() + SYNTHETIC_KEY.encode())
        self.assert_error('credential-in-image')
        self.assertFalse(FakeConnection.calls)
        self.assertFalse((Path(self.args['output_dir']) / 'image-01.png').exists())

    def test_more_invalid_response_shapes(self):
        cases = [b'null', b'[]', b'{"model":"qwen3.8-27b","model":"other"}', b'{"x":NaN}']
        cases += [json.dumps({**SYNTHETIC_RESPONSE, **change}).encode() for change in (
            {'choices': [None]}, {'choices': [{'finish_reason': 'stop', 'message': None}]},
            {'choices': [{'finish_reason': 'stop', 'message': {'content': ['not text']}}]},
            {'choices': [{'finish_reason': 'stop', 'message': {'content': 'text', 'tool_calls': [{}]}}]},
            {'choices': [{'finish_reason': 'stop', 'message': {'content': 'x' * (client.MAX_FINDINGS + 1)}}]},
        )]
        for i, raw in enumerate(cases):
            self.args['output_dir'] = str(self.root / f'shape-{i}')
            FakeConnection.response = raw
            self.assertEqual(self.invoke()['status'], 'error')
        self.assertEqual(len(FakeConnection.calls), len(cases))

    def test_cli_subprocess_synthetic_success_and_network_block(self):
        # Only this test harness injects the fake; production CLI has no transport flag.
        script = (
            'import sys,socket,http.client; '
            'sys.path.insert(0,sys.argv[1]); '
            'from test_inspect import FakeConnection,deny_socket; '
            'socket.socket=deny_socket; '
            'http.client.HTTPConnection=FakeConnection; '
            'import cli; raise SystemExit(cli.main([]))'
        )
        env = {'PATH': os.environ.get('PATH', ''), 'LITELLM_API_KEY': SYNTHETIC_KEY,
               'PYTHONDONTWRITEBYTECODE': '1'}
        p = subprocess.run([sys.executable, '-B', '-c', script, str(Path(__file__).parent)],
                           input=json.dumps(self.args), capture_output=True, text=True, env=env, timeout=20)
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertIn('SYNTHETIC', json.loads(p.stdout)['findings'])
        self.assertEqual(p.stderr, '')

    def test_cli_rejects_oversized_input(self):
        with patch.object(sys, 'stdin', io.StringIO(' ' * (client.MAX_INPUT_BYTES + 1))), contextlib.redirect_stdout(io.StringIO()) as output:
            self.assertEqual(cli.main([]), 1)
        self.assertEqual(json.loads(output.getvalue())['error'], 'invalid-input-json')
        self.assertFalse(FakeConnection.calls)

    def test_cli_main_success_and_error(self):
        for expected in (0, 1):
            with patch.object(sys, 'stdin', io.StringIO(json.dumps(self.args))), contextlib.redirect_stdout(io.StringIO()) as output:
                code = cli.main([])
            self.assertEqual(code, expected)
            self.assertEqual(json.loads(output.getvalue())['status'], 'ok' if expected == 0 else 'error')
        self.assertEqual(len(FakeConnection.calls), 1)

    def test_cli_usage_error_does_not_echo_arbitrary_arguments(self):
        p = subprocess.run([sys.executable, '-B', str(ROOT / 'cli.py'), '--model', SYNTHETIC_KEY],
                           capture_output=True, text=True,
                           env={'PYTHONDONTWRITEBYTECODE': '1'}, timeout=20)
        self.assertEqual(p.returncode, 2)
        self.assertNotIn(SYNTHETIC_KEY, p.stdout + p.stderr)
        self.assertEqual(p.stderr, 'paper-vision: invalid command-line arguments\n')

    def test_cli_subprocess_exit_codes_without_network(self):
        # Inherited environment is scrubbed; real credentials/config are never read.
        env = {'PATH': os.environ.get('PATH', ''), 'PYTHONDONTWRITEBYTECODE': '1'}
        for data in ('bad json', json.dumps({**self.args, 'output_dir': str(self.root / 'cli-error')})):
            p = subprocess.run([sys.executable, '-B', str(ROOT / 'cli.py')], input=data,
                               capture_output=True, text=True, env=env, timeout=20)
            self.assertEqual(p.returncode, 1, p.stderr)
            self.assertEqual(json.loads(p.stdout)['status'], 'error')
            self.assertEqual(p.stderr, '')


if __name__ == '__main__':
    unittest.main()
