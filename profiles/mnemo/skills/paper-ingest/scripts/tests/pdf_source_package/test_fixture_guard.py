"""External retained fixture bundles must be protected before test setup writes."""
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


class FixtureGuard(unittest.TestCase):
    def test_external_bundle_is_protected_before_and_after_configure(self):
        support = Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp).resolve(); bundle = root/'bundle'; bundle.mkdir()
            manifest = bundle/'manifest.json'; manifest.write_text('{}\n')
            for configure in (False, True):
                code = ('import sys; from pathlib import Path; sys.path.insert(0, sys.argv[1]); '
                        'import offline_test_support as support; ')
                if configure:
                    code += 'support.configure(Path(sys.argv[3])); '
                code += 'Path(sys.argv[2]).write_text("must not overwrite")'
                result = subprocess.run([sys.executable, '-B', '-c', code, str(support),
                                         str(manifest), str(root/'scratch')],
                    env=dict(os.environ, PAPER_INGEST_FIXTURE_BUNDLE=str(bundle)),
                    capture_output=True, text=True)
                self.assertNotEqual(result.returncode, 0, result.stdout+result.stderr)
                self.assertIn('protected-test-input:', result.stderr)
                self.assertEqual(manifest.read_text(), '{}\n')


if __name__ == '__main__':
    unittest.main()
