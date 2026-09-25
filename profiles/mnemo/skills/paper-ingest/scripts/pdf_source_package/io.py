"""Explicit paths and durable artifacts; no process-global output directory."""
from pathlib import Path
import hashlib
import json
import os
import sys

SETTINGS = dict(model='qwen3.8-27b', temperature=0,
                response_format={'type': 'json_object'}, max_tokens=65536)
TIMEOUT = 1200
LIMIT = 262144
ASSETS = Path(__file__).parent / 'assets'


def require(ok, reason):
    if not ok:
        raise ValueError(reason)


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def dumps(value):
    return (json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + '\n').encode()


def strict(raw):
    def pairs(items):
        value = {}
        for key, item in items:
            require(key not in value, 'duplicate-json-key:' + key)
            value[key] = item
        return value
    def constant(s):
        raise ValueError('nonfinite-json:' + s)
    return json.loads(raw, object_pairs_hook=pairs, parse_constant=constant)


def load(path):
    return strict(Path(path).read_bytes())


def safe(root, relative):
    root = Path(root).absolute()
    relative = Path(relative)
    require(not relative.is_absolute() and '..' not in relative.parts and '\\' not in str(relative), 'unsafe-relative-path')
    p = root / relative
    require(not any(x.is_symlink() for x in (p, *p.parents)), 'symlink-output-forbidden')
    require(p.resolve().is_relative_to(root.resolve()), 'path-escape')
    require(not p.is_file() or p.stat().st_nlink == 1, 'hardlink-output-forbidden')
    return p


def outside_retention(path):
    p = Path(path).absolute()
    require(not any((parent/"retention.json").exists() for parent in (p, *p.parents)), "write-inside-immutable-retention")
    return p


def put(path, raw, replace=False):
    p = outside_retention(path)
    require(not any(x.is_symlink() for x in (p, *p.parents)), 'symlink-output-forbidden')
    require(not p.is_file() or p.stat().st_nlink == 1, 'hardlink-output-forbidden')
    p.parent.mkdir(parents=True, exist_ok=True)
    raw = raw.encode() if isinstance(raw, str) else raw
    tmp = p.with_name(p.name + f'.tmp-{os.getpid()}') if replace else p
    with tmp.open('xb') as stream:
        stream.write(raw)
        stream.flush()
        os.fsync(stream.fileno())
    if replace:
        os.replace(tmp, p)
    fd = os.open(p.parent, os.O_RDONLY)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)
    return p


def save(path, value, replace=False):
    return put(path, dumps(value), replace)


def code_hashes():
    root = Path(__file__).parent
    return {str(p.relative_to(root)): sha(p) for p in sorted(root.rglob('*'))
            if p.is_file() and p.suffix in ('.py', '.txt', '.json')}


def offline():
    """Inherited by CLI subprocesses through PDF_SOURCE_PACKAGE_OFFLINE."""
    os.environ['PDF_SOURCE_PACKAGE_OFFLINE'] = '1'
    os.environ['HF_HUB_OFFLINE'] = '1'
    os.environ['TRANSFORMERS_OFFLINE'] = '1'
    def deny(event, args):
        if event.startswith('socket.'):
            raise RuntimeError('offline-network-blocked:' + event)
    sys.addaudithook(deny)
