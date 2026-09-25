"""Offline historical-reader regressions; never sends a model request.

Run `python -B -m unittest test_compatibility` with the package, adapter scripts,
and this test directory on PYTHONPATH. Set PDF_ENRICHMENT_METHOD,
REENRICH_ENRICHMENT_ROOT, REENRICH_INTEGRATION_ROOT to trusted code roots;
SOURCE_PACKAGE_TEST_ROOT and TMPDIR to existing nonsymlink scratch paths;
PDF_ENRICHMENT_OFFLINE=1 and PDF_SOURCE_PACKAGE_OFFLINE=1.
"""
import copy
import json
from pathlib import Path
import tempfile
import unittest
import subprocess
import sys
from unittest.mock import patch

from pdf_enrichment import bindings, trusted, requests
from pdf_enrichment.io import sha, digest, dumps
from qualified_enrichment import reviews, exports
import article_enrichment as ae
import reenrich as rr
import portable_articles as pa
import source_package as source
import test_reenrich as fixtures


class PortableCompatibility(unittest.TestCase):
    setUp = fixtures.ReenrichTests.setUp
    plan = fixtures.ReenrichTests.plan
    ready = fixtures.ReenrichTests.ready

    def test_fresh_process_loads_only_explicitly_configured_packages(self):
        self.ready()
        _, _, manifest, _, _, binding, _ = rr.context(self.work)
        code = ('import sys; sys.path.insert(0, '+repr(str(Path(ae.__file__).parent))+'); '
                'from pathlib import Path; import article_enrichment as ae; '
                'ae.verify_export(Path('+repr(str(self.work))+'), '+repr(binding)+', Path('+repr(str(manifest))+'))')
        result = subprocess.run([sys.executable, '-B', '-E', '-c', code], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_unknown_count_and_dossier_formats_rejected(self):
        self.ready()
        _, _, manifest, _, _, binding, _ = rr.context(self.work)
        path = self.work/'enrichment/counts.json'; original = path.read_bytes()
        value = pa.load(path); value['schema'] = 'portable-count-v999'
        path.write_text(json.dumps(value)); path.with_suffix('.json.sha256').write_text(sha(path))
        with self.assertRaisesRegex(ValueError, 'unsupported.*format'):
            ae.verify_counts(path.parent, pa.load(path.parent/'prepared.json'))
        path.write_bytes(original); path.with_suffix('.json.sha256').write_text(sha(path))
        path = self.work/'review/dossier.json'; value = pa.load(path)
        value['schema'] = 'portable-review-dossier-v999'
        path.write_text(json.dumps(value)); path.with_suffix('.json.sha256').write_text(sha(path))
        with self.assertRaisesRegex(ValueError, 'unsupported.*format'):
            ae.review_verify(self.work, binding, manifest)

    def test_completed_export_survives_code_change_but_execution_stays_bound(self):
        self.ready()
        _, _, manifest, _, _, binding, _ = rr.context(self.work)
        saved = pa.load(self.work/'export/handoff.json')
        changed = copy.deepcopy(ae.code_bindings())
        changed['portable-adapter-v2']['article_runtime.py'] = '0'*64
        with patch.object(ae, 'code_bindings', return_value=changed):
            self.assertEqual(ae.verify_export(self.work, binding, manifest), saved)
            self.assertEqual(rr.execute(work_root=self.work)['next_step'], 'candidate-import')
            with self.assertRaisesRegex(ValueError, 'code-changed'):
                ae.verify(self.work, binding, manifest)

    def test_unknown_prepared_format_rejected_even_with_valid_byte_seal(self):
        self.plan(); rr.advance(self.work, 'prepare')
        _, _, manifest, _, _, binding, _ = rr.context(self.work)
        path = self.work/'enrichment/prepared.json'
        value = pa.load(path); value['schema'] = 'portable-enrichment-plan-v999'
        path.write_text(json.dumps(value)); path.with_suffix('.json.sha256').write_text(sha(path))
        with self.assertRaisesRegex(ValueError, 'unsupported.*format'):
            ae.verify(self.work, binding, manifest)

    def test_uncertain_request_remains_uncertain_and_cannot_resume_after_code_change(self):
        self.plan(); rr.advance(self.work, 'prepare')
        approval = fixtures.count_and_approve(self.work, self.base)
        rr.advance(self.work, 'approved-execute', approval=approval,
                   fixture_transport=fixtures.inference_double(self.work, interrupt=True))
        _, _, manifest, _, _, binding, _ = rr.context(self.work)
        changed = copy.deepcopy(ae.code_bindings())
        changed['portable-adapter-v2']['article_runtime.py'] = '0'*64
        with patch.object(ae, 'code_bindings', return_value=changed):
            state = ae.execution_state(self.work, binding, manifest)
            self.assertEqual(state['accounting']['counts']['uncertain'], 1)
            self.assertFalse(state['accounting']['complete'])
            with self.assertRaisesRegex(ValueError, 'code-changed'):
                rr.advance(self.work, 'approved-execute', approval=approval,
                           fixture_transport=lambda *a: self.fail('unexpected replay'))

    def test_historical_read_still_rejects_outcome_and_request_tampering(self):
        self.ready()
        _, _, manifest, _, _, binding, _ = rr.context(self.work)
        root = self.work/'enrichment/requests/r000001'
        for name in ('request-wire.json', 'response-body.json', 'outcome.json'):
            path = root/name; original = path.read_bytes()
            try:
                path.write_bytes(original+b' ')
                with self.assertRaises(ValueError): ae.verify_export(self.work, binding, manifest)
            finally:
                path.write_bytes(original)


class LegacyCompatibility(unittest.TestCase):
    def test_diagnostic_reader_preserves_producer_hashes_not_changed_source(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp).resolve()
            saved = dict(schema=pa.DIAGNOSTIC_SCHEMA, roster=['element'], files=[dict(key='package/manifest.json')],
                         provenance=dict(method_code={'old.py':'1'*64}), source_status={'complete':False})
            current = copy.deepcopy(saved); current['provenance']['method_code'] = {'new.py':'2'*64}
            with patch.object(pa, 'verify_local', return_value=(saved, {'package/manifest.json':root/'manifest.json'})), \
                 patch.object(pa, '_diagnostic_value', return_value=(current, {})):
                self.assertEqual(pa.verify_diagnostic(root/'unused'), saved['source_status'])
                current['source_status'] = {'complete':True}
                with self.assertRaisesRegex(ValueError, 'recomputation-mismatch'):
                    pa.verify_diagnostic(root/'unused')

    def test_historical_launcher_accepts_retired_paths_and_interpreter_symlink(self):
        from qualified_enrichment.launcher import Deployment, argv_for
        import sys
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp).resolve()
            python = root/'python'; python.symlink_to(sys.executable)
            deployment = Deployment(root/'retired', root/'enrichment', root/'method', root/'adapter', python)
            args = dict(operation='export', review_root=str(root/'review'), output=str(root/'export'))
            command = argv_for(args, deployment, root/'attempt', historical=True)
            self.assertEqual(command[0], str(python))
            with self.assertRaisesRegex(ValueError, 'trusted-deployment'):
                argv_for(args, deployment, root/'attempt')

    def test_v7_reader_pins_format_and_preserves_execution_binding(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp).resolve(); source_root = root/'source'; source_root.mkdir()
            run = root/'run'; run.mkdir()
            plan = dict(schema='pdf-source-package-enrichment-v7', stage='enrichment-prepare-v7',
                prompt_version='enrichment-prompts-v7', response_schema='enrichment-response-v7',
                settings=requests.SETTINGS, model=requests.MODEL, requests=[], documents=[],
                kinds=[], selection=[], fixture=True,
                code={'old.py':'1'*64}, method={'root':'/unavailable/historical/method','code':{'old.py':'2'*64}},
                source_package={'root':str(source_root),'tree_sha256':'source-hash'})
            def save():
                (run/'enrichment-plan.json').write_text(json.dumps(plan))
                (run/'plan.sha256').write_text(sha(run/'enrichment-plan.json'))
            save()
            with patch('pdf_enrichment.package_io.SourcePackage') as package, \
                 patch('pdf_enrichment.accounting.accounting'), \
                 patch.object(trusted, 'code_hashes', return_value={'new.py':'3'*64}):
                package.return_value.snapshot = {'tree_sha256':'source-hash'}
                package.return_value.documents = []
                self.assertEqual(bindings.verify(run, for_execution=False), plan)
                with self.assertRaisesRegex(ValueError, 'enrichment-code-changed'):
                    bindings.verify(run)
                element = {'id':'element'}
                row = dict(id='request', element_id='element', element_sha256=digest(dumps(element)),
                           document='doc', kind='table', caption_only=False, directory='request')
                (run/'request').mkdir(); (run/'request/prompt.txt').write_text(requests.PROMPTS['table'])
                plan['requests'] = [row]; save()
                package.return_value.documents = [{'elements':[element]}]
                with patch.object(bindings, 'request', return_value=({'source':'original'}, {'payload':'original'})), \
                     patch.object(requests, 'build_request', return_value=({'payload':'original'}, {'source':'original'})) as builder:
                    self.assertEqual(bindings.verify(run, for_execution=False), plan)
                    builder.return_value = ({'payload':'different semantics'}, {'source':'original'})
                    with self.assertRaisesRegex(ValueError, 'incompatible-enrichment-payload'):
                        bindings.verify(run, for_execution=False)
                plan['stage'] = 'enrichment-prepare-v999'; save()
                with self.assertRaisesRegex(ValueError, 'unsupported.*format'):
                    bindings.verify(run, for_execution=False)

    def test_dossier_and_export_retain_provenance_after_code_change(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp).resolve(); run = root/'run'; run.mkdir(); src = root/'source'; src.mkdir()
            state = dict(path=str(run), kind='v7-run', source_package=str(src),
                         source_bindings={}, elements=[], execution_holds=[], fixture=True, documents=[])
            with patch.object(reviews, 'snapshot', return_value=state):
                dossier = reviews.create(run, 'v7-run', root/'review')
                exports.export(root/'review', root/'export')
                saved = json.loads((root/'export/handoff.json').read_text())
                with patch.object(reviews, 'code_hashes', return_value={'changed.py':'0'*64}), \
                     patch.object(exports, 'code_hashes', return_value={'changed.py':'0'*64}):
                    self.assertEqual(reviews.verify(root/'review'), dossier)
                    self.assertEqual(exports.verify_export(root/'export/handoff.json', production=False), saved)
                altered = copy.deepcopy(state); altered['source_bindings'] = {'changed':'0'*64}
                with patch.object(reviews, 'snapshot', return_value=altered):
                    with self.assertRaisesRegex(ValueError, 'stale-source'):
                        reviews.verify(root/'review')

    def test_export_reconstructs_decisions_once(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp).resolve(); run=root/'run'; run.mkdir(); src=root/'source'; src.mkdir()
            state=dict(path=str(run),kind='v7-run',source_package=str(src),source_bindings={},
                       elements=[],execution_holds=[],fixture=True,documents=[])
            with patch.object(reviews,'snapshot',return_value=state):
                reviews.create(run,'v7-run',root/'review')
                with patch.object(reviews,'apply',wraps=reviews.apply) as apply:
                    exports.build(root/'review')
                    print('EXPORT-REVIEW-APPLICATIONS',apply.call_count)
                    self.assertEqual(apply.call_count,1)
                # Standalone review-chain validation still checks semantics.
                with patch.object(reviews,'apply',side_effect=ValueError('invalid review')):
                    with self.assertRaisesRegex(ValueError,'invalid review'):
                        reviews.decisions(root/'review',pa.load(root/'review/dossier.json'))

    def test_v7_read_reuses_source_but_rechecks_its_bytes(self):
        from qualified_enrichment import runtime
        from pdf_enrichment.io import tree_hash
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp).resolve(); run=root/'run'; run.mkdir(); src=root/'source'; src.mkdir()
            plan=dict(schema='pdf-source-package-enrichment-v7',stage='enrichment-prepare-v7',
                prompt_version='enrichment-prompts-v7',response_schema='enrichment-response-v7',
                settings=requests.SETTINGS,model=requests.MODEL,requests=[],documents=[],kinds=[],selection=[],fixture=True,
                code={'old.py':'1'*64},method={'root':'/retired/method','code':{'old.py':'2'*64}},
                source_package=dict(root=str(src),tree_sha256=tree_hash(src)['tree_sha256']))
            (run/'enrichment-plan.json').write_text(json.dumps(plan)); (run/'plan.sha256').write_text(sha(run/'enrichment-plan.json'))
            with patch('pdf_enrichment.package_io.SourcePackage') as pkg, \
                 patch.object(runtime,'SourcePackage',pkg),patch('pdf_enrichment.accounting.accounting'):
                pkg.return_value.root=src; pkg.return_value.snapshot=tree_hash(src)
                pkg.return_value.documents=[];pkg.return_value.eligible_elements.return_value=[]
                result=runtime.read_run(run)
                print('V7-SOURCE-RECONSTRUCTIONS',pkg.call_count)
                self.assertEqual(pkg.call_count,1);self.assertEqual(result['source_bindings'],{})
                def changed(*args):
                    (src/'changed.txt').write_text('Mutation during outcome verification')
                    return {},[]
                with patch.object(runtime,'outcomes',side_effect=changed):
                    with self.assertRaisesRegex(ValueError,'source-changed-during-read'):
                        runtime.read_run(run)

    def test_source_handoff_keeps_recorded_code_provenance(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp).resolve()
            saved = dict(schema='source-package-handoff-v1', production_complete=True,
                status='production-mechanical-complete', retention='unused', package='unused',
                launcher_result='unused', summary='summary', method_bindings={'old.py':'1'*64})
            (root/'handoff.json').write_text(json.dumps(saved)); (root/'summary.txt').write_text('summary')
            current = dict(saved, method_bindings={'new.py':'2'*64})
            with patch.object(source, 'build_handoff', return_value=current):
                self.assertEqual(source.verify_handoff(root/'handoff.json', root/'method'), saved)
            current = dict(current, summary='changed scientific result')
            with patch.object(source, 'build_handoff', return_value=current):
                with self.assertRaises(ValueError): source.verify_handoff(root/'handoff.json', root/'method')


if __name__ == '__main__':
    unittest.main()
