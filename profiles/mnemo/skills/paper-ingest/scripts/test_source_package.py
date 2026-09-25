#!/usr/bin/env python3
"""Offline public-CLI integration. Inputs and all writes require explicit scratch.

Run with the trusted PDF interpreter, SOURCE_PACKAGE_TEST_ROOT (existing scratch)
and SOURCE_PACKAGE_FIXTURE (JSON: source, sha256, page_count, method). The fixture
PDF must be a verified copy of a genuine retained source. No network/model calls.
"""
import copy
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from typing import Any

SCRIPT = Path(__file__).parent / 'source_package.py'
ROOT = Path(os.environ['SOURCE_PACKAGE_TEST_ROOT'])
FIX = json.loads(Path(os.environ['SOURCE_PACKAGE_FIXTURE']).read_text())

def digest(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def save(p, data):
    Path(p).write_text(json.dumps(data, indent=2) + '\n')

def run(*args):
    result = subprocess.run([sys.executable, '-B', str(SCRIPT), *map(str, args)],
                            cwd=ROOT, text=True, capture_output=True, timeout=180)
    return result.returncode, result.stdout + result.stderr

def manifest(base) -> dict[str, Any]:
    body = base/'body.txt'; body.write_text('Synthetic body acquisition fixture, not scientific evidence.')
    diagnostic = base/'failed.txt'; diagnostic.write_bytes(b'Synthetic transport: 503 unavailable')
    nonpdf = base/'data.csv'; nonpdf.write_bytes(b'synthetic,value\na,1\n')
    def item(ident, path, role, fmt):
        return dict(id=ident, path=str(path), sha256=digest(path), filename=path.name,
                    role=role, format=fmt, source_url='https://example.invalid/article',
                    discovery_url='https://example.invalid/article', article_slug='fixture-paper',
                    identity_verification=dict(status='operator-verified', basis='Explicit offline fixture binding, not scientific verification'))
    return dict(schema='acquired-sources-v1',
        article=dict(slug='fixture-paper', title='Fixture paper', doi='10.9999/fixture', pmid=None, version='fixture'),
        files=[item('main', Path(FIX['source']), 'manuscript', 'pdf'), item('body', body, 'body', 'other'),
               item('data', nonpdf, 'supplement', 'other')],
        attempts=[dict(id='failed', route='synthetic-test', outcome='failed', source_url='https://example.invalid/supp',
                       observed_at='not-recorded', raw_response='available', limitation='Synthetic transport response',
                       artifacts=[dict(path=str(diagnostic), sha256=digest(diagnostic))])],
        obligations=dict(body=dict(status='retrieved', file_ids=['body']), manuscript=dict(status='retrieved', file_ids=['main'])),
        attachments=dict(status='advertised', inspected_url='https://example.invalid/article',
                         items=[dict(id='data', status='retrieved', file_id='data', observed_link='https://example.invalid/data', filename='data.csv'),
                                dict(id='missing', status='missing', attempt_ids=['failed'], disposition='Unavailable; synthetic transport test',
                                     observed_link='https://example.invalid/supp', filename='supp.pdf')]))

class SyntheticCompletionPolicyTests(unittest.TestCase):
    """Synthetic unit states only, never saved as workflow or model evidence."""
    def setUp(self):
        import source_package
        self.adapter = source_package
        self.tmp = tempfile.TemporaryDirectory(prefix='synthetic-policy-', dir=ROOT)
        self.addCleanup(self.tmp.cleanup)
        self.base = Path(self.tmp.name)
        self.retention = {'acquisition': {
            'article': {'slug': 'synthetic-unit-control'},
            'obligations': {'body': {'status': 'retrieved'}, 'manuscript': {'status': 'retrieved'}},
            'attachments': {'status': 'none-listed', 'items': []}, 'files': []}}
        self.state = {'fixture': False, 'requested_work_complete': True,
            'documents': [{'complete_package': True}],
            'facts': {'phases': {phase: {'status': 'complete', 'uncertain_reservations': 0,
                                       'fixture_or_replay_calls': 0}
                                 for phase in ('initial', 'classification', 'association')},
                      'inspection': {'status': 'not-supplied', 'uncertain_reservations': 0,
                                     'fixture_or_replay_calls': 0}}}

    def synthetic_handoff(self):
        # Mock only for this policy unit control. No files, model responses,
        # launcher receipts or successful execution evidence are fabricated.
        from unittest.mock import patch
        paths = {key: str(self.base/key) for key in ('facts_path', 'results_path', 'summary_path')}
        with patch.object(self.adapter, 'verified_state', return_value=(
                self.retention, self.state, 'Synthetic unit control, not workflow evidence.', None)), \
                patch.object(self.adapter, 'sha', return_value='synthetic-unit-not-a-hash'), \
                patch.object(self.adapter, 'tree_hashes', return_value={}), \
                patch.object(self.adapter, 'load', return_value=paths):
            return self.adapter.build_handoff(self.base/'retention.json', self.base/'package',
                                              self.base/'result.json', self.base/'method')

    def test_otherwise_complete_nonfixture_positive_control(self):
        self.assertEqual(self.adapter.holds_for(self.retention, self.state, self.base), [])
        handoff = self.synthetic_handoff()
        self.assertTrue(handoff['production_complete'])
        self.assertEqual(handoff['status'], 'production-mechanical-complete')
        self.assertEqual(handoff['holds'], [])

    def test_retained_nonpdf_is_visible_limitation_not_hold(self):
        row = {'id': 'data', 'role': 'supplement', 'format': 'other',
               'extraction_disposition': 'deferred-non-PDF'}
        self.retention['acquisition']['files'].append(row)
        self.retention['acquisition']['attachments'] = {
            'status': 'advertised', 'items': [{'status': 'retrieved', 'file_id': 'data'}]}
        before = copy.deepcopy(self.retention)
        self.assertEqual(self.adapter.holds_for(self.retention, self.state, self.base), [])
        handoff = self.synthetic_handoff()
        self.assertTrue(handoff['production_complete'])
        self.assertEqual(handoff['sources']['files'], [row])
        self.assertTrue(any('data' in text and 'Non-PDF extraction deferred' in text
                            for text in handoff['limitations']))
        self.assertEqual(self.retention, before)

    def test_missing_advertised_attachment_remains_hold(self):
        self.retention['acquisition']['attachments'] = {
            'status': 'advertised', 'items': [{'status': 'missing',
                'disposition': 'Synthetic acquisition failure; not a real retrieval'}]}
        self.assertIn('advertised-attachments-missing',
                      self.adapter.holds_for(self.retention, self.state, self.base))
        with self.assertRaisesRegex(ValueError, 'advertised-attachments-missing'):
            self.synthetic_handoff()

    def test_incomplete_uncertain_fixture_and_replay_remain_holds(self):
        cases = [
            ('requested-work-incomplete', lambda s: s.update(requested_work_complete=False)),
            ('incomplete-full-document-package', lambda s: s['documents'][0].update(complete_package=False)),
            ('phase-hold-initial', lambda s: s['facts']['phases']['initial'].update(status='incomplete')),
            ('phase-hold-initial', lambda s: s['facts']['phases']['initial'].update(uncertain_reservations=1)),
            ('fixture-not-production', lambda s: s.update(fixture=True)),
            ('fixture-or-replay-initial', lambda s: s['facts']['phases']['initial'].update(fixture_or_replay_calls=1)),
            ('inspection-evidence-incomplete', lambda s: s['facts']['inspection'].update(uncertain_reservations=1)),
            ('fixture-inspection-not-production', lambda s: s['facts']['inspection'].update(fixture_or_replay_calls=1)),
        ]
        original = copy.deepcopy(self.state)
        for expected, change in cases:
            with self.subTest(hold=expected):
                self.state = copy.deepcopy(original)
                change(self.state)
                self.assertIn(expected, self.adapter.holds_for(self.retention, self.state, self.base))
                with self.assertRaisesRegex(ValueError, expected):
                    self.synthetic_handoff()


class RetentionTests(unittest.TestCase):
    def setUp(self):
        self.base = Path(tempfile.mkdtemp(prefix='retention-', dir=ROOT))
        self.input = self.base/'input.json'
        self.value = manifest(self.base)
        self.output = self.base/'retained'

    def prepare(self, expected=0):
        save(self.input, self.value)
        code, out = run('prepare', '--input', self.input, '--output', self.output,
                        '--application-endpoint', 'https://example.invalid/v1/chat/completions', '--max-application-posts', 100)
        self.assertEqual(code, expected, out)
        return out

    def test_exact_retention_and_default_scope(self):
        self.prepare()
        scope = json.loads((self.output/'scope.json').read_text())
        doc = scope['documents'][0]
        self.assertEqual(digest(doc['source']), FIX['sha256'])
        self.assertEqual(doc['page_count'], FIX['page_count'])
        self.assertEqual(doc['pages'], list(range(1, FIX['page_count']+1)))
        self.assertEqual(doc['channels'], ['caption','figure','structured','classification','association'])
        retained = json.loads((self.output/'retention.json').read_text())
        self.assertEqual(retained['acquisition']['attachments'], self.value['attachments'])
        for row in retained['bindings']:
            self.assertEqual(digest(self.output/row), retained['bindings'][row])
        self.assertEqual(len(retained['acquisition']['files']), 3)
        self.assertFalse(any(self.output.rglob('*approval*')))
        self.prepare(expected=2)

    def test_invalid_sources(self):
        for kind in ('hash', 'identity', 'duplicate', 'page-count', 'symlink', 'escape', 'filename', 'duplicate-content'):
            with self.subTest(kind=kind):
                value = copy.deepcopy(self.value)
                if kind == 'hash': value['files'][0]['sha256'] = '0'*64
                if kind == 'identity': value['files'][0]['article_slug'] = 'wrong-paper'
                if kind == 'duplicate': value['files'].append(copy.deepcopy(value['files'][0]))
                if kind == 'page-count': value['files'][0]['page_count'] = 999
                if kind == 'symlink':
                    p = self.base/'linked.pdf'; p.symlink_to(FIX['source']); value['files'][0]['path'] = str(p)
                if kind == 'escape': value['files'][0]['path'] = str(self.base/'../input.pdf')
                if kind == 'filename': value['files'][0]['filename'] = '../escape.pdf'
                if kind == 'duplicate-content':
                    row = copy.deepcopy(value['files'][0]); row['id'] = 'duplicate-content'; value['files'].append(row)
                save(self.input, value)
                code, out = run('prepare', '--input', self.input, '--output', self.base/('bad-'+kind),
                                '--application-endpoint', 'https://example.invalid/v1/chat/completions', '--max-application-posts', 100)
                self.assertEqual(code, 2, out)

    def test_pdf_supplement_cannot_be_deferred_as_non_pdf(self):
        main=self.value['files'].pop(0)
        supplement=self.value['files'][-1]
        supplement.update(path=main['path'],sha256=main['sha256'],filename='supplement.pdf')
        self.value['obligations']['manuscript']=dict(status='missing',attempt_ids=[],disposition='Offline negative fixture')
        output=self.prepare(expected=2)
        self.assertIn('PDF cannot be declared non-PDF',output)

    def test_observed_anchor_link_is_preserved(self):
        self.value['files'][0]['discovery_url']='https://example.invalid/article#supplementary-information'
        self.prepare()
        retained=json.loads((self.output/'retention.json').read_text())
        self.assertEqual(retained['acquisition']['files'][0]['discovery_url'],self.value['files'][0]['discovery_url'])

    def test_selected_scope_and_implicit_authorization_rejected(self):
        for field,value in [('pages',[1]),('channels',['figure'])]:
            self.value['files'][0][field]=value
            self.prepare(expected=2)
            del self.value['files'][0][field]
        self.assertEqual(run('execute','--authorize-posts')[0],2)

    def test_output_symlink_and_hardlink_rejected(self):
        self.output=self.base/'linked-output'; self.output.symlink_to(self.base,target_is_directory=True)
        self.prepare(expected=2)
        linked=self.base/'hardlinked.pdf'; os.link(FIX['source'],linked)
        try:
            self.value['files'][0]['path']=str(linked)
            self.output=self.base/'hardlink-output'; self.prepare(expected=2)
        finally:
            linked.unlink()

    def test_explicit_budget_and_endpoint_required(self):
        save(self.input, self.value)
        self.assertEqual(run('prepare','--input',self.input,'--output',self.output)[0], 2)

    def test_attachment_states_and_missing_obligations(self):
        for status in ('not-inspected','none-listed'):
            self.value['files'] = self.value['files'][:2]
            self.value['attachments'] = dict(status=status, inspected_url='https://example.invalid/article',items=[])
            self.output = self.base/status
            self.prepare()
        self.value['obligations']['body'] = dict(status='missing', disposition='Not retrieved', attempt_ids=['failed'])
        self.value['files'] = [row for row in self.value['files'] if row['role'] != 'body']
        self.output = self.base/'missing-body'; self.prepare()

class WorkflowTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.base = Path(tempfile.mkdtemp(prefix='workflow-', dir=ROOT))
        value = manifest(cls.base)
        save(cls.base/'input.json', value)
        code, out = run('prepare','--input',cls.base/'input.json','--output',cls.base/'retained',
                        '--application-endpoint','https://example.invalid/v1/chat/completions','--max-application-posts',100)
        if code: raise AssertionError(out)
        cls.package = cls.base/'package'
        cls.workflow('prepare','--scope-path',cls.base/'retained/scope.json','--output-dir',cls.package,'--offline-fixture')
        cls.failed_report = cls.workflow('report','--package-dir',cls.package,expected=1)
        cls.workflow('finalize','--package-dir',cls.package,expected=1)
        cls.result = cls.workflow('summary','--package-dir',cls.package,'--output-dir',cls.base/'summary')

    @classmethod
    def workflow(cls, operation, *args, expected=0):
        attempt = cls.base/('attempt-'+operation)
        result = subprocess.run([sys.executable,'-B','-m','pdf_source_package.launcher',operation,
                                *map(str,args),'--attempt-dir',str(attempt),'--offline'],
                                cwd=FIX['method'],capture_output=True,text=True,timeout=180)
        if result.returncode != expected: raise AssertionError(result.stdout+result.stderr)
        return attempt/'result.json'

    def handoff(self, expected=0, test_only=True):
        output = self.base/('handoff-'+str(len(list(self.base.glob('handoff-*')))))
        args = ['handoff','--retention',self.base/'retained/retention.json','--package',self.package,
                '--launcher-result',self.result,'--method',FIX['method'],'--output',output]
        if test_only: args += ['--test-only-root',ROOT]
        code, out = run(*args)
        self.assertEqual(code, expected, out)
        return output

    def test_offline_end_to_end_and_production_rejection(self):
        result = json.loads(self.result.read_text())
        self.assertTrue(result['success'])
        self.assertFalse(result['requested_work_complete'])
        output = self.handoff()
        handoff = json.loads((output/'handoff.json').read_text())
        self.assertEqual(handoff['status'], 'test-only')
        self.assertFalse(handoff['production_complete'])
        self.assertEqual((output/'summary.txt').read_text(), (self.base/'summary/summary.txt').read_text())
        self.assertTrue(handoff['holds'])
        self.assertNotIn('non-PDF-supplement-extraction-deferred', handoff['holds'])
        retained_data = next(row for row in handoff['sources']['files'] if row['id'] == 'data')
        self.assertEqual(retained_data['extraction_disposition'], 'deferred-non-PDF')
        self.assertTrue(any('Non-PDF extraction deferred: data.' in text for text in handoff['limitations']))
        self.assertEqual(run('verify','--handoff',output/'handoff.json','--method',FIX['method'])[0], 2)
        self.handoff(expected=2, test_only=False)

    def test_failed_report_not_rescued_by_later_summary(self):
        current=self.result
        try:
            self.result=self.failed_report
            self.handoff(expected=2)
        finally: self.result=current

    def test_real_verifier_rejects_fixture_handoff(self):
        output=self.handoff()
        brain=self.base/'verify-brain'; (brain/'papers').mkdir(parents=True,exist_ok=True); (brain/'people').mkdir(exist_ok=True)
        pointer=os.path.relpath(output/'handoff.json',brain/'papers')
        (brain/'papers/fixture-paper.md').write_text('---\nkind: paper\nslug: fixture-paper\ntitle: Fixture paper\ndoi: 10.9999/fixture\nauthors: []\nlinks: []\n---\n\n## Ingest log\n\nSource package: '+pointer+'\n')
        result=subprocess.run([sys.executable,'-B',str(SCRIPT.parent/'verify_ingest.py'),'fixture-paper',
            '--instance',str(brain),'--offline','--ledgerless','--source-package-handoff',str(output/'handoff.json'),
            '--source-package-method',FIX['method']],cwd=ROOT,text=True,capture_output=True,timeout=60)
        self.assertEqual(result.returncode,1,result.stdout+result.stderr)
        self.assertIn('handoff is not production completion',result.stdout)

    def test_output_cannot_modify_package_or_retention(self):
        for output in (self.package/'handoff',self.base/'retained/handoff',self.result.parent/'handoff'):
            code,out=run('handoff','--retention',self.base/'retained/retention.json','--package',self.package,
                '--launcher-result',self.result,'--method',FIX['method'],'--output',output,'--test-only-root',ROOT)
            self.assertEqual(code,2,out)
            self.assertFalse(output.exists())

    def test_stale_corrupt_or_failed_evidence_rejected(self):
        for target, change in [
            (self.result, lambda v: v.update(exit_code=7)),
            (self.result, lambda v: v.update(requested_work_complete=True)),
            (self.base/'attempt-summary/process.json', lambda v: v.update(process_status='running',exit_code=None)),
            (self.base/'summary/facts.json', lambda v: v.update(requested_work_complete=True)),
            (self.package/'manifest.json', lambda v: v['documents'][0].update(identity='wrong')),
            (self.package/'manifest.json', lambda v: v['documents'][0].update(page_count=999)),
            (self.package/'manifest.json', lambda v: v['documents'][0].update(channels=['figure'])),
            (self.package/'manifest.json', lambda v: v['documents'][0].update(selected_pages=[1])),
        ]:
            with self.subTest(target=target):
                raw = target.read_bytes()
                try:
                    value = json.loads(raw); change(value); save(target,value)
                    self.handoff(expected=2)
                finally: target.write_bytes(raw)

    def test_changed_retained_original_rejected(self):
        scope = json.loads((self.base/'retained/scope.json').read_text()); p=Path(scope['documents'][0]['source'])
        raw=p.read_bytes()
        try:
            p.write_bytes(raw+b'changed'); self.handoff(expected=2)
        finally: p.write_bytes(raw)

    def test_unknown_reservation_stale_summary_rejected(self):
        row=json.loads((self.package/'initial-plan.json').read_text())['requests'][0]
        p=self.package/row['directory']/'reservation.json'
        try:
            save(p,dict(request_sha256=row['request_sha256'],transport_origin='synthetic-offline-test',state='reserved-may-have-posted'))
            self.handoff(expected=2)
        finally: p.unlink()

class VersionedHandoffTests(unittest.TestCase):
    def test_v1_remains_verifiable_but_cannot_satisfy_new_route(self):
        import source_package as adapter
        from unittest.mock import patch
        with tempfile.TemporaryDirectory(prefix='v1-read-',dir=ROOT) as folder:
            base=Path(folder)
            value=dict(schema='source-package-handoff-v1',production_complete=True,
                       status='production-mechanical-complete',retention=str(base/'retention.json'),
                       package=str(base/'package'),launcher_result=str(base/'result.json'),
                       summary='Synthetic boundary only.',article={'slug':'fixture-paper'})
            save(base/'handoff.json',value); (base/'summary.txt').write_text(value['summary'])
            with patch.object(adapter,'build_handoff',return_value=value):
                self.assertEqual(adapter.verify_handoff(base/'handoff.json',base/'method'),value)
                with self.assertRaisesRegex(ValueError,'requires enriched handoff'):
                    adapter.verify_handoff(base/'handoff.json',base/'method',require_enriched=True)
                (base/'summary.txt').write_text('tampered')
                with self.assertRaisesRegex(ValueError,'summary changed'):
                    adapter.verify_handoff(base/'handoff.json',base/'method')


if __name__ == '__main__':
    sys.addaudithook(lambda event,args: (_ for _ in ()).throw(RuntimeError('offline-network-blocked')) if event.startswith('socket.') else None)
    unittest.main(verbosity=2)
