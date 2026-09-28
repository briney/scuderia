from test_jobs import Jobs, only_local_tests
from manuscript_ingest import workflow as w
import importlib
from pathlib import Path
import json

class Campaign(Jobs):
    def module(self):
        return importlib.import_module('manuscript_ingest.campaign')
    def test_scan_uses_frontmatter_and_reports_parse_errors(self):
        c=self.module()
        self.page.write_text(self.page.read_text().replace('needs-ingest: true','needs-ingest: false')+'needs-ingest: true\n')
        stub=self.page.parent/'stub.md'; stub.write_text(self.page.read_text().replace('needs-ingest: false','needs-ingest: true'))
        bad=self.page.parent/'broken.md'; bad.write_text('---\ntags: [unterminated\n---\n')
        before={p:p.read_bytes() for p in self.page.parent.iterdir()}
        result=c.scan_queue(self.brain)
        self.assertEqual([r['path'] for r in result['items']],[str(stub)])
        self.assertEqual([r['path'] for r in result['diagnostics']],[str(bad)])
        self.assertEqual(before,{p:p.read_bytes() for p in self.page.parent.iterdir()})

def load_tests(loader,tests,pattern):return only_local_tests(__name__)
