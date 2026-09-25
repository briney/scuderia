"""Small trusted-import and file contracts for portable article operations.

Trusted code roots are explicit operator configuration, never archive data.
No module substitution, credential discovery, or arbitrary command hooks.
"""
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
    require(p.is_absolute() and '..' not in p.parts and '\\' not in str(p), 'absolute-nonsymlink-path-required')
    require(not any(x.is_symlink() for x in (p, *p.parents)), 'symlink-forbidden')
    if p.exists() and not p.is_dir():
        s = p.stat()
        require(stat.S_ISREG(s.st_mode) and s.st_nlink == 1, 'regular-single-link-file-required')
    return p


def relative_key(value):
    require(isinstance(value, str) and bool(value) and len(value) <= 1024, 'relative-key-required')
    parts = value.split('/')
    require(all(re.fullmatch(r'[A-Za-z0-9_][A-Za-z0-9_.+@=-]*', s) and
                not s.endswith(('.', '.lock')) for s in parts), 'unsafe-relative-key:' + value)
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
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False,
                                    separators=(',', ':'), allow_nan=False).encode()).hexdigest()


def tree(root):
    root = absolute(root)
    result = {}
    for p in sorted(root.rglob('*')):
        absolute(p)
        if p.is_file() and '__pycache__' not in p.parts and not p.name.endswith(('.pyc', '.lock')):
            result[str(p.relative_to(root))] = sha(p)
    return result


def external(output, roots):
    output = absolute(output)
    for r in roots:
        r = absolute(r)
        require(not output.is_relative_to(r) and not r.is_relative_to(output), 'unsafe-output-overlap')
    return output


def trusted_modules():
    names = (('PDF_ENRICHMENT_METHOD', 'pdf_source_package'),
             ('REENRICH_ENRICHMENT_ROOT', 'pdf_enrichment'),
             ('REENRICH_INTEGRATION_ROOT', 'qualified_enrichment'))
    roots = {}
    sys.dont_write_bytecode = True
    for env, name in names:
        value = os.environ.get(env)
        require(value, 'trusted-root-required:' + env)
        root = absolute(value)
        require((root / name / '__init__.py').is_file(), 'trusted-module-missing:' + name)
        if str(root) not in sys.path:
            sys.path.insert(0, str(root))
        module = importlib.import_module(name)
        require(Path(module.__file__).resolve().parent == root / name, 'different-trusted-module-loaded:' + name)
        roots[name] = root
    return roots


def code_bindings():
    roots = trusted_modules()
    bindings = {name: {k: v for k, v in tree(root / name).items()
                       if k.endswith(('.py', '.json', '.txt'))} for name, root in roots.items()}
    here = Path(__file__).parent
    bindings['portable-adapter-v2'] = {n: sha(here / n) for n in
        ('article_runtime.py', 'portable_articles.py', 'reenrich.py', 'article_enrichment.py', 'final_products.py')
        if (here / n).is_file()}
    return bindings


@contextmanager
def locked(root):
    root = absolute(root)
    p = absolute(root / 'operation.lock')
    with p.open('a+b') as stream:
        fcntl.flock(stream, fcntl.LOCK_EX | fcntl.LOCK_NB)
        yield
