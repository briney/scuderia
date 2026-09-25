"""Standalone native PDF source packages. Importing never accesses an endpoint."""
import os
from .io import offline
if os.environ.get('PDF_SOURCE_PACKAGE_OFFLINE') == '1':
    offline()
__version__ = '0.1.0'
