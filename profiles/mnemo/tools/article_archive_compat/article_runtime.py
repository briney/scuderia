"""Historical read-only dependency closure; extracted without changing validation contracts."""
from contextlib import contextmanager
import fcntl
import hashlib
import importlib
import json
import os
from pathlib import Path
import re
import stat
import sys

def require(ok, reason):
    if not ok:
        raise ValueError(reason)

def absolute(value):
    require(isinstance(value, (str, Path)) and bool(str(value)), 'absolute-path-required')
    p = Path(value)
    require(p.is_absolute() and '..' not in p.parts and ('\\' not in str(p)), 'absolute-nonsymlink-path-required')
    for component in (p, *p.parents):
        require(not component.is_symlink(), f'symlink-forbidden:{p}:component={component}')
    if p.exists() and (not p.is_dir()):
        s = p.stat()
        require(stat.S_ISREG(s.st_mode) and s.st_nlink == 1, 'regular-single-link-file-required')
    return p

def relative_key(value):
    require(isinstance(value, str) and bool(value) and (len(value) <= 1024), 'relative-key-required')
    parts = value.split('/')
    require(all((re.fullmatch('[A-Za-z0-9_][A-Za-z0-9_.+@=-]*', s) and (not s.endswith(('.', '.lock'))) for s in parts)), 'unsafe-relative-key:' + value)
    require(str(Path(value)) == value, 'noncanonical-relative-key')
    return value

def inside(root, key):
    root = absolute(root)
    p = absolute(root / relative_key(key))
    require(p.is_relative_to(root), 'path-escape')
    return p

def sha(path):
    h = hashlib.sha256()
    p = absolute(path)
    with p.open('rb') as stream:
        for block in iter(lambda : stream.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()

def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(',', ':'), allow_nan=False).encode()).hexdigest()

def external(output, roots):
    output = absolute(output)
    for r in roots:
        r = absolute(r)
        require(not output.is_relative_to(r) and (not r.is_relative_to(output)), 'unsafe-output-overlap')
    return output

def trusted_modules():
    """Historical verification uses only these packaged readers; never load executors."""
    return {}

@contextmanager
def locked(root):
    root = absolute(root)
    p = absolute(root / 'operation.lock')
    with p.open('a+b') as stream:
        fcntl.flock(stream, fcntl.LOCK_EX | fcntl.LOCK_NB)
        yield

def outside_instance(path):
    """Article payloads and operation state belong outside a bound brain vault."""
    path = absolute(path)
    require(not any(((parent / 'instance.yaml').is_file() for parent in (path, *path.parents))), 'article-work-must-be-outside-instance:' + str(path))
    return path
