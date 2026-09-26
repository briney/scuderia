"""Bounded inference with serial reservations/results; synthetic sources only."""
import json
import os
from pathlib import Path
import threading
import unittest
from unittest.mock import patch

import pymupdf
from pdf_source_package import execution, gates, preparation
from pdf_source_package.io import load, save, sha, SETTINGS
import test_bookkeeping as source_fixtures
import test_reenrich as enrichment_fixtures
import reenrich as rr
import article_enrichment as ae


class Scheduling(unittest.TestCase):
    def test_limit_refill_and_serial_callbacks(self):
        from pdf_source_package.concurrency import run_requests
        for limit in (1, 3, 8):
            with self.subTest(limit=limit):
                barrier = threading.Barrier(limit, timeout=5)
                owner = threading.get_ident(); prepared = []; results = []; threads = set()
                def prepare(row):
                    self.assertEqual(threading.get_ident(), owner)
                    prepared.append(row)
                    return row
                def request(row):
                    threads.add(threading.get_ident())
                    barrier.wait()
                    return row * 2
                def consume(row, future):
                    self.assertEqual(threading.get_ident(), owner)
                    results.append(future.result())
                run_requests(range(limit * 2), prepare, request, consume, vlm_concurrency=limit)
                self.assertEqual(prepared, list(range(limit * 2)))
                self.assertEqual(sorted(results), list(range(0, limit * 4, 2)))
                self.assertEqual(len(threads), limit)

    def test_stop_drains_active_without_reserving_pending(self):
        from pdf_source_package.concurrency import run_requests
        barrier = threading.Barrier(3, timeout=5); release = threading.Event()
        prepared = []; recorded = []
        def prepare(row): prepared.append(row); return row
        def request(row):
            barrier.wait()
            if row: self.assertTrue(release.wait(5))
            return row
        def consume(row, future):
            recorded.append(future.result())
            if row == 0:
                release.set()
                raise ValueError('shared-failure')
        with self.assertRaisesRegex(ValueError, 'shared-failure'):
            run_requests(range(8), prepare, request, consume, vlm_concurrency=3)
        self.assertEqual(prepared, [0, 1, 2])
        self.assertEqual(sorted(recorded), [0, 1, 2])

    def test_completion_during_serial_processing_precedes_refill(self):
        from concurrent.futures import ThreadPoolExecutor
        from pdf_source_package.concurrency import run_requests
        barrier = threading.Barrier(3, timeout=5)
        release = threading.Event(); failed_done = threading.Event(); prepared = []; recorded = []
        submit = ThreadPoolExecutor.submit
        def tracked_submit(pool, fn, item):
            future = submit(pool, fn, item)
            if item == 1: future.add_done_callback(lambda _: failed_done.set())
            return future
        def prepare(row): prepared.append(row); return row
        def request(row):
            if row < 3: barrier.wait()
            if row in (1, 2): self.assertTrue(release.wait(5))
            if row == 1: raise ValueError('shared-failure')
            return row
        def consume(row, future):
            recorded.append(row)
            result = future.result()
            if result == 0:
                release.set()
                self.assertTrue(failed_done.wait(5))
        with patch.object(ThreadPoolExecutor, 'submit', tracked_submit):
            with self.assertRaisesRegex(ValueError, 'shared-failure'):
                run_requests(range(6), prepare, request, consume, vlm_concurrency=3)
        self.assertEqual(prepared, [0, 1, 2])
        self.assertEqual(sorted(recorded), [0, 1, 2])

    def test_prepare_failure_drains_already_dispatched(self):
        from pdf_source_package.concurrency import run_requests
        recorded = []
        def prepare(row):
            if row == 1: raise ValueError('reservation-failed')
            return row
        with self.assertRaisesRegex(ValueError, 'reservation-failed'):
            run_requests(range(5), prepare, lambda row: row,
                         lambda row, future: recorded.append(future.result()))
        self.assertEqual(recorded, [0])

    def test_configuration(self):
        from pdf_source_package.concurrency import concurrency_limit
        with patch.dict(os.environ, {}, clear=True):
            self.assertEqual(concurrency_limit(), 3)
        with patch.dict(os.environ, {'PAPER_INGEST_VLM_CONCURRENCY': '12'}):
            self.assertEqual(concurrency_limit(), 12)
            self.assertEqual(concurrency_limit(4), 4)
        for invalid in (0, -1, True, 1.5, '3'):
            with self.subTest(invalid=invalid), self.assertRaises(ValueError):
                concurrency_limit(invalid)
        with patch.dict(os.environ, {'PAPER_INGEST_VLM_CONCURRENCY': '0'}):
            with self.assertRaises(ValueError): concurrency_limit()

    def test_setting_provenance(self):
        from pdf_source_package.concurrency import concurrency_settings
        with patch.dict(os.environ, {}, clear=True):
            self.assertEqual(concurrency_settings(), dict(vlm_concurrency=3, concurrency_source='fallback'))
        with patch.dict(os.environ, {'PAPER_INGEST_VLM_CONCURRENCY': '12'}):
            self.assertEqual(concurrency_settings(), dict(vlm_concurrency=12, concurrency_source='environment'))
            self.assertEqual(concurrency_settings(4), dict(vlm_concurrency=4, concurrency_source='argument'))


class SourceExecution(unittest.TestCase):
    setUp = source_fixtures.Bookkeeping.setUp
    counted = source_fixtures.Bookkeeping.counted

    def prepared(self):
        with pymupdf.open() as pdf:
            for _ in range(6): pdf.new_page().insert_text((40, 40), 'Synthetic source text.')
            pdf.save(self.pdf)
        scope = load(self.scope); scope['max_application_posts'] = 6
        scope['documents'][0]['sha256'] = sha(self.pdf); save(self.scope, scope, replace=True)
        preparation.prepare(self.scope, self.job, fixture=True)
        self.counted(self.job, 'initial', self.root)
        from pdf_source_package.counting import MODEL_REPO, REVISION
        cache = Path(os.environ['PDF_PROCESSOR_CACHE'])
        assets = cache/('models--'+MODEL_REPO.replace('/', '--'))/'snapshots'/REVISION
        plan = load(self.job/'initial-plan.json')
        plan['processor'] = dict(cache=str(cache), files={p.name: sha(p) for p in assets.iterdir() if p.is_file()})
        save(self.job/'initial-plan.json', plan, replace=True)
        approval = gates.seal(self.job, 'initial')
        approval.update(approved=True, approved_by='Synthetic test', source_and_candidates_reviewed=True,
                        payload_counts_reviewed=True, current_route_reviewed=True)
        path = self.root/'approval.json'; save(path, approval)
        return path

    def test_shared_failure_drains_active_and_leaves_pending_unreserved(self):
        approval = self.prepared(); barrier = threading.Barrier(3, timeout=5)
        released = threading.Event(); sent = []; original_save = execution.save
        def record(path, *args, **kwargs):
            result = original_save(path, *args, **kwargs)
            if Path(path).name == 'stop.json': released.set()
            return result
        def transport(payload, row):
            sent.append(row['id']); barrier.wait()
            if row['page'] == 1: return dict(http_status=401, raw=b'{}')
            self.assertTrue(released.wait(5))
            return dict(http_status=400, raw=b'{}')
        transport.origin = 'offline-inference-double'
        with patch.object(execution, 'save', side_effect=record):
            self.assertEqual(execution.run_phase(self.job, 'initial', approval, transport=transport, vlm_concurrency=3), 1)
        self.assertEqual(len(sent), 3)
        requests = self.job/'requests'
        self.assertEqual(len(list(requests.glob('*/reservation.json'))), 3)
        self.assertEqual(len(list(requests.glob('*/output-bindings.json'))), 3)
        self.assertEqual(len(list(requests.glob('*/response-body.json'))), 3)
        from pdf_source_package.workflow import final_state
        self.assertFalse(final_state(self.job)['requested_work_complete'])

    def test_default_overlap_serial_export_and_no_retry(self):
        approval = self.prepared(); barrier = threading.Barrier(3, timeout=5)
        owner = threading.get_ident(); sent = []; decoder = execution.decode_export
        def transport(payload, row):
            sent.append(row['id']); barrier.wait()
            content = dict(page=row['page'], objects=[], uncertainty=None, empty_reason='Synthetic empty page')
            return dict(http_status=200, raw=json.dumps(dict(model=SETTINGS['model'],
                choices=[dict(finish_reason='stop', message=dict(content=json.dumps(content)))],
                usage=dict(prompt_tokens=12))).encode())
        transport.origin = 'offline-inference-double'
        def decode(*args):
            self.assertEqual(threading.get_ident(), owner)
            return decoder(*args)
        with patch.object(execution, 'decode_export', side_effect=decode):
            self.assertEqual(execution.run_phase(self.job, 'initial', approval, transport=transport, vlm_concurrency=3), 0)
        self.assertEqual(len(sent), len(set(sent)))
        self.assertEqual(len(sent), 6)
        self.assertEqual(len(list((self.job/'requests').glob('*/output-bindings.json'))), 6)
        with self.assertRaisesRegex(ValueError, 'phase-already-complete'):
            execution.run_phase(self.job, 'initial', approval, transport=transport, vlm_concurrency=3)

    def test_source_inherits_environment_and_records_origin(self):
        approval = self.prepared()
        def transport(payload, row):
            return dict(http_status=400, raw=b'{}')
        transport.origin = 'offline-inference-double'
        with patch.dict(os.environ, {'PAPER_INGEST_VLM_CONCURRENCY': '12'}):
            execution.run_phase(self.job, 'initial', approval, transport=transport)
        session = load(self.job/'initial-session.json')
        self.assertEqual((session['vlm_concurrency'], session['concurrency_source']), (12, 'environment'))


class EnrichmentExecution(unittest.TestCase):
    setUp = enrichment_fixtures.ReenrichTests.setUp
    plan = enrichment_fixtures.ReenrichTests.plan

    def test_overlap_and_serial_outcomes(self):
        self.plan(selected=False); rr.advance(self.work, 'prepare')
        approval = enrichment_fixtures.count_and_approve(self.work, self.base)
        good = enrichment_fixtures.inference_double(self.work)
        barrier = threading.Barrier(2, timeout=5); owner = threading.get_ident()
        sent = []; assemble = ae._response
        def transport(payload, row):
            sent.append(row['id']); barrier.wait()
            return good(payload, row)
        def response(*args):
            self.assertEqual(threading.get_ident(), owner)
            return assemble(*args)
        with patch.object(ae, '_response', side_effect=response):
            with patch.dict(os.environ, {'PAPER_INGEST_VLM_CONCURRENCY': '12'}):
                state = rr.advance(self.work, 'approved-execute', approval=approval, fixture_transport=transport)
        self.assertEqual(state['accounting']['counts']['completed'], 2)
        self.assertEqual(load(self.work/'enrichment/execution-start.json')['concurrency_source'], 'environment')
        self.assertEqual(len(sent), len(set(sent)))
        again = rr.advance(self.work, 'approved-execute', approval=approval,
                           fixture_transport=lambda *a: self.fail('consumed request reposted'),vlm_concurrency=4)
        self.assertEqual(again, state)
        self.assertEqual(ae.execution_settings(self.work)['vlm_concurrency'],4)
        self.assertEqual(ae.execution_settings(self.work)['concurrency_source'],'argument')
        self.assertEqual(load(self.work/'enrichment/execution-start.json')['vlm_concurrency'],12)
        for row in load(self.work/'enrichment/prepared.json')['requests']:
            d=self.work/'enrichment'/row['directory']
            result=load(d/'outcome.json')
            self.assertLessEqual(load(d/'reservation.json')['started_at'],result['response_received_at'])
            self.assertLessEqual(result['response_received_at'],result['ended_at'])

    def test_fatal_response_retains_other_active_outcome(self):
        self.plan(selected=False); rr.advance(self.work, 'prepare')
        approval = enrichment_fixtures.count_and_approve(self.work, self.base)
        good = enrichment_fixtures.inference_double(self.work)
        barrier = threading.Barrier(2, timeout=5); release = threading.Event()
        original_seal = ae._seal_file
        def record(path, value):
            result = original_seal(path, value)
            if path.name == 'failure.json': release.set()
            return result
        def transport(payload, row):
            barrier.wait()
            if row['id'] == 'r000001': return dict(http_status=401, raw=b'{}')
            self.assertTrue(release.wait(5))
            return good(payload, row)
        with patch.object(ae, '_seal_file', side_effect=record):
            with self.assertRaises(ValueError):
                rr.advance(self.work, 'approved-execute', approval=approval, fixture_transport=transport)
        _, _, manifest, _, _, binding, _ = rr.context(self.work)
        state = ae.execution_state(self.work, binding, manifest)['accounting']
        self.assertEqual(state['counts'], dict(pending=0, uncertain=0, failed=1, completed=1))
        self.assertTrue(state['integrity_hold'])
        with self.assertRaisesRegex(ValueError, 'integrity-hold'):
            rr.advance(self.work, 'approved-execute', approval=approval,
                       fixture_transport=lambda *a: self.fail('fatal execution resumed'))


class Interfaces(unittest.TestCase):
    setUp = source_fixtures.Bookkeeping.setUp

    def test_native_launchers_and_source_cli_forward_override(self):
        import sys
        from pdf_source_package import launcher, cli
        from qualified_enrichment import launcher as enrichment_launcher
        scripts = Path(execution.__file__).parents[1]
        self.job.mkdir(parents=True); approval = self.root/'approval.json'; approval.write_text('{}')
        args = dict(operation='execute', package_dir=str(self.job), phase='initial',
                    approval_path=str(approval), authorize_posts=True,
                    attempt_dir=str(self.root/'source-attempt'), vlm_concurrency=12)
        def child(argv, cwd, attempt, timeout):
            self.assertEqual(argv[-2:], ['--vlm-concurrency', '12'])
            with patch.object(execution, 'run_phase', return_value=0) as run:
                # The evidence export needs a real package; exercise the execute CLI separately.
                command = argv[argv.index('execute'):]
                self.assertEqual(cli.main(command), 0)
                self.assertEqual(run.call_args.kwargs['vlm_concurrency'], 12)
            attempt.mkdir()
            return dict(exit_code=0, process_status='exited')
        with patch.object(launcher, 'run_child', side_effect=child):
            launcher.launch(args, launcher.Deployment(scripts, Path(sys.executable)))
        deployment = enrichment_launcher.Deployment(scripts, scripts, scripts, scripts, Path(sys.executable))
        enrichment_args = dict(operation='execute', job=str(self.job), approval=str(approval),
                               authorize_posts=True, attempt_dir=str(self.root/'enrichment-attempt'), vlm_concurrency=8)
        argv = enrichment_launcher.argv_for(enrichment_args, deployment, self.root/'enrichment-attempt')
        self.assertIn('--vlm-concurrency=8', argv)
        for value in (True, 0, -1, 1.5, '3'):
            with self.subTest(value=value), self.assertRaises(ValueError):
                launcher.validated(dict(args, vlm_concurrency=value))
            with self.subTest(value=value), self.assertRaises(ValueError):
                enrichment_launcher.argv_for(dict(enrichment_args, vlm_concurrency=value), deployment, self.root/'enrichment-attempt')

    def test_plugin_refresh_does_not_reuse_prior_launcher_cache(self):
        import hashlib
        import runpy
        import sys
        import types
        scripts = Path(execution.__file__).parents[1]
        workflow = runpy.run_path(str(scripts/'paper-workflow/__init__.py'))
        enrichment = runpy.run_path(str(scripts/'paper-enrichment/__init__.py'))
        old_source = '_paper_workflow_method_' + hashlib.sha256(str(scripts).encode()).hexdigest()[:16]
        old_enrichment = '_paper_enrichment_launcher_' + hashlib.sha256(str(scripts/'qualified_enrichment/launcher.py').encode()).hexdigest()[:16]
        stale = types.ModuleType('prior_launcher')
        package = types.ModuleType(old_source); package.__path__ = []
        with patch.dict(sys.modules, {old_source: package, old_source+'.launcher': stale, old_enrichment: stale}):
            for module in (workflow, enrichment):
                loaded = module['runner'](str(scripts))
                self.assertIsNot(loaded, stale)
                self.assertTrue(callable(loaded.launch))
