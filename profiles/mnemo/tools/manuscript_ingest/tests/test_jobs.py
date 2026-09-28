import json
from pathlib import Path
import sys
import tempfile
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from manuscript_ingest import workflow

class Jobs(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(); self.root=Path(self.temp.name).resolve()
        self.brain=self.root/'brain'; (self.brain/'papers').mkdir(parents=True)
        (self.brain/'instance.yaml').write_text('name: fixture\n')
        self.page=self.brain/'papers/paper.md'; self.page.write_text('---\nkind: paper\nslug: paper\ntitle: Synthetic experiment\ndoi: 10.1234/synthetic\nneeds-ingest: true\n---\n# Synthetic experiment\n')
        self.runtime=self.root/'runtime'; self.runtime.mkdir()
        (self.runtime/'config.json').write_text(json.dumps(dict(instance=str(self.brain),archive=dict(remote='fixture',bucket='fixture',prefix='article-packages'))))
    def tearDown(self): self.temp.cleanup()
    def test_reuse_and_scope(self):
        a=workflow.start(self.page,runtime_root=self.runtime)
        b=workflow.start(self.page,runtime_root=self.runtime)
        self.assertEqual(a['job_id'],b['job_id'])
        self.assertEqual(set(a),{'job_id','status','next_action','artifacts','warnings','blocking_reason'})
        self.assertFalse(Path(a['artifacts']['work']).is_relative_to(self.brain))
        self.assertEqual(workflow.load_job(a['job_id'],self.runtime)['scope'],'manuscript-to-page')
        with self.assertRaises(ValueError): workflow.status('../escape',runtime_root=self.runtime)
    def test_inside_brain_refused(self):
        with self.assertRaisesRegex(ValueError,'outside'):
            workflow.start(self.page,runtime_root=self.brain/'runtime')
    def test_changed_identity_conflict(self):
        workflow.start(self.page,runtime_root=self.runtime)
        with self.assertRaisesRegex(ValueError,'identity'):
            workflow.start(self.page,runtime_root=self.runtime,identity=dict(doi='10.1234/other'))

def only_local_tests(module_name):
    """Run each declared case once; inherited fixture helpers are not extra tests."""
    module=sys.modules[module_name]; suite=unittest.TestSuite()
    for value in vars(module).values():
        if isinstance(value,type) and issubclass(value,unittest.TestCase) and value.__module__==module_name:
            for name in value.__dict__:
                if name.startswith('test_'):suite.addTest(value(name))
    return suite


def load_tests(loader,tests,pattern):return only_local_tests(__name__)
