"""Shared primitives for the enrichment stage.

Deliberately minimal: hashing, strict JSON, durable writes, path safety,
offline hook. These mirror the accepted method's conventions but are
independent (the accepted method must remain byte-identical; we only read
its saved packages).
"""
from pathlib import Path
import hashlib
import json
import os
import sys


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


def tree_hash(root):
    """Stable hash over every file name+content below root (immutability checks)."""
    root = Path(root)
    require(root.is_dir(), 'tree-hash-root')
    entries = {}
    for p in sorted(x for x in root.rglob('*') if x.is_file()):
        entries[str(p.relative_to(root))] = sha(p)
    h = hashlib.sha256()
    for name in sorted(entries):
        h.update(name.encode()); h.update(entries[name].encode())
    return dict(tree_sha256=h.hexdigest(), file_count=len(entries), files=entries)


def dumps(value):
    return (json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + '\n').encode()


def strict(raw):
    """Strict JSON: duplicate keys, non-finite constants rejected."""
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
    """Sandboxed relative path inside an output run directory."""
    root = Path(root).absolute()
    relative = Path(relative)
    require(not relative.is_absolute() and '..' not in relative.parts and '\\' not in str(relative),
            'unsafe-relative-path')
    p = root / relative
    require(not any(x.is_symlink() for x in (p, *p.parents)), 'symlink-output-forbidden')
    require(p.resolve().is_relative_to(root.resolve()), 'path-escape')
    return p


def put(path, raw, replace=False):
    p = Path(path).absolute()
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
    fd=os.open(p.parent,os.O_RDONLY)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)
    return p


def save(path, value, replace=False):
    return put(path, dumps(value), replace)


def offline():
    """Inherited by CLI subprocesses through PDF_ENRICHMENT_OFFLINE."""
    os.environ['PDF_ENRICHMENT_OFFLINE'] = '1'
    os.environ['HF_HUB_OFFLINE'] = '1'
    os.environ['TRANSFORMERS_OFFLINE'] = '1'
    def deny(event, args):
        if event.startswith('socket.'):
            raise RuntimeError('offline-network-blocked:' + event)
    sys.addaudithook(deny)


def now_utc():
    from datetime import datetime, timezone
    return datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')


STAGE = 'pdf-source-package-enrichment-v7'
