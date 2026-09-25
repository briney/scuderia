"""Import accepted primitives from an explicitly trusted, read-only method path."""
from pathlib import Path
import importlib
import os
import sys
from .io import require, sha


def method_path(path=None):
    value = path or os.environ.get('PDF_ENRICHMENT_METHOD')
    require(value, 'trusted-method-path-required')
    require(Path(value).is_absolute(), 'trusted-method-path-must-be-absolute')
    root=Path(value).resolve()
    require(root.is_absolute() and (root/'pdf_source_package/counting.py').is_file(), 'trusted-method-missing')
    return root


def module(name, path=None):
    root=method_path(path)
    loaded=sys.modules.get('pdf_source_package')
    if loaded is not None:
        require(Path(loaded.__file__).resolve().parent == root/'pdf_source_package', 'different-method-already-imported')
    sys.path.insert(0,str(root)) if str(root) not in sys.path else None
    mod=importlib.import_module('pdf_source_package.'+name)
    require(Path(mod.__file__).resolve().is_relative_to(root), 'method-import-path-mismatch')
    return mod


def read_method_path():
    """Use operator configuration or the already pinned import, never archive code paths."""
    loaded = sys.modules.get('pdf_source_package')
    return method_path(Path(loaded.__file__).resolve().parent.parent if loaded else None)


def validate_code_provenance(value):
    """Hashes describe the producer; they neither select code nor authorize execution."""
    require(isinstance(value, dict) and value, 'invalid-code-provenance')
    for name, item in value.items():
        require(isinstance(name, str) and name, 'invalid-code-provenance')
        if isinstance(item, dict):
            validate_code_provenance(item)
        else:
            require(isinstance(item, str) and len(item) == 64 and
                    all(c in '0123456789abcdef' for c in item), 'invalid-code-provenance')
    return value


def code_hashes():
    root=Path(__file__).parent
    return {p.name:sha(p) for p in sorted(root.glob('*.py'))}


def method_hashes(path):
    root=method_path(path)/'pdf_source_package'
    return {str(p.relative_to(root)):sha(p) for p in sorted(root.rglob('*'))
            if p.is_file() and p.suffix in ('.py','.json','.txt')}
