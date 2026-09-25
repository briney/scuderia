"""Offline semantic assertions using retained records, never live inference."""
import copy
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from qualified_enrichment.records import project
import os
FIXTURES = Path(os.environ['PDF_ENRICHMENT_FIXTURES'])/'replays'


def retained(relative):
    request = FIXTURES/relative
    ev = json.loads((request/'source-evidence.json').read_bytes())
    outcome = json.loads((request/'outcome.json').read_bytes())
    return dict(element_id=ev['element_id'], source_sha256=ev['source_sha256'],
                evidence=ev, outcome=outcome)


class PropagationTests(unittest.TestCase):
    def test_existing_native_algorithm_notation_findings_are_not_empty(self):
        element = retained('v7/algorithm-native/requests/e0085-algorithm')
        before = copy.deepcopy(element)
        result = project(element)
        self.assertTrue(result['findings'], 'Existing uncertain algorithm state must propagate without operator findings')
        self.assertEqual(result['review_status'], 'unreviewed')
        self.assertEqual(element, before)
        self.assertTrue(any('/lines/' in f['target'] for f in result['findings']))


if __name__ == '__main__':
    sys.addaudithook(lambda event, args: (_ for _ in ()).throw(RuntimeError('offline-network-blocked'))
                     if event.startswith('socket.') else None)
    unittest.main(verbosity=2)
