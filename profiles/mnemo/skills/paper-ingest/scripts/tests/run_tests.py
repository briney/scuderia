"""Offline enrichment unittest suite; optional exact-count checks use --processor-cache."""
import argparse
import json
from pathlib import Path
import sys
import tempfile
import unittest

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from offline_test_support import configure, release_protection


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--scratch', type=Path)
    parser.add_argument('--evidence', type=Path)
    parser.add_argument('--suite-dir', type=Path, default=HERE/'pdf_source_package')
    parser.add_argument('--name', default='offline')
    parser.add_argument('--processor-cache', type=Path)
    args = parser.parse_args()
    for path in (args.scratch,args.evidence):
        if path and path.exists():
            parser.error('scratch and evidence must be new directories')
    with tempfile.TemporaryDirectory(prefix='enrichment-tests-') as temporary:
        scratch = (args.scratch or Path(temporary)).resolve()
        fixtures = None
        if args.suite_dir.resolve() in (HERE/'pdf_source_package', HERE/'paper_vision'):
            fixtures = scratch/'inputs'; fixtures.mkdir(parents=True)
        configure(scratch, adapter=HERE.parent, processor_cache=args.processor_cache, fixtures=fixtures)
        suite = unittest.defaultTestLoader.discover(str(args.suite_dir), pattern='test_*.py')
        result = unittest.TextTestRunner(verbosity=2).run(suite)
        successful=result.wasSuccessful() and result.testsRun>0
        if args.evidence:
            args.evidence.mkdir(parents=True, exist_ok=True)
            (args.evidence/'test-summary.json').write_text(json.dumps(dict(name=args.name, exit=0 if successful else 1, counts=dict(tests=result.testsRun,
                failures=len(result.failures), errors=len(result.errors), skipped=len(result.skipped))))+'\n')
        release_protection()
        return 0 if successful else 1


if __name__ == '__main__':
    raise SystemExit(main())
