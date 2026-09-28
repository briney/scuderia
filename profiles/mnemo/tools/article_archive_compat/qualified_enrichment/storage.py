"""Historical read-only dependency closure; extracted without changing validation contracts."""
from pathlib import Path
from .records import require

def absolute(value):
    require(isinstance(value, (str, Path)) and bool(str(value)), 'absolute-path-required')
    path = Path(value)
    require(path.is_absolute() and '..' not in path.parts and ('\\' not in str(path)), 'absolute-path-without-traversal-required')
    require(not any((p.is_symlink() for p in (path, *path.parents))), 'symlink-forbidden')
    require(not path.is_file() or path.stat().st_nlink == 1, 'hardlink-forbidden')
    return path
