"""Exclusive artifact writes; reuse frozen IO, reject redirected evidence paths."""
from pathlib import Path
from pdf_enrichment.io import load, save, put, sha, offline, now_utc
from .records import require, digest


def absolute(value):
    require(isinstance(value, (str, Path)) and bool(str(value)), 'absolute-path-required')
    path = Path(value)
    require(path.is_absolute() and '..' not in path.parts and '\\' not in str(path), 'absolute-path-without-traversal-required')
    require(not any(p.is_symlink() for p in (path, *path.parents)), 'symlink-forbidden')
    require(not path.is_file() or path.stat().st_nlink == 1, 'hardlink-forbidden')
    return path


def tree(root):
    root = absolute(root)
    require(root.is_dir(), 'missing-evidence-directory')
    result = {}
    for path in sorted(root.rglob('*')):
        absolute(path)
        if path.is_file() and '__pycache__' not in path.parts:
            result[str(path.relative_to(root))] = sha(path)
    return result


def external(output, protected):
    output = absolute(output)
    for value in protected:
        path = absolute(value)
        require(not output.is_relative_to(path) and not path.is_relative_to(output), 'output-overlaps-protected-evidence')
    return output


def new(output, protected=()):
    output = external(output, protected)
    require(output.parent.is_dir(), 'output-parent-must-exist')
    output.mkdir(mode=0o700)
    return output


def code_hashes():
    package = Path(__file__).absolute().parent
    result = {'qualified_enrichment/'+name: value for name, value in tree(package).items()}
    for name in ('entry.py', 'operate.py', 'paper-enrichment/__init__.py', 'paper-enrichment/plugin.yaml'):
        result[name] = sha(absolute(package.parent/name))
    return result


def bound_file(path):
    path = absolute(path)
    return dict(path=str(path), sha256=sha(path))
