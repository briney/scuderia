#!/usr/bin/env python3
"""Real selective-enrichment integration: selected IDs reach frozen v7.

Builds the actual source-to-v1 handoff route offline (mirroring the retained
PARENT fixture method, not inventing a new one), then drives
qualified_enrichment.runtime.prepare with a SELECTED subset of elements and
verifies the v7 enrichment plan contains exactly the selected roster.

This is a synthetic offline fixture route (OFFLINE-FIXTURE); it never posts,
never claims production, and consumes zero model requests.

Run with the trusted PDF interpreter (see test_portable_articles.py header);
requires the uncertainty-integration tree on PYTHONPATH ( Integration root ).
"""
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).parent
sys.path.insert(0, str(SCRIPTS))
sys.addaudithook(lambda event, args: (_ for _ in ()).throw(RuntimeError('offline-network-blocked'))
                 if event.startswith('socket.') else None)

ROOT = Path(os.environ['SOURCE_PACKAGE_TEST_ROOT'])
METHOD = Path(os.environ['PDF_ENRICHMENT_METHOD'])
INTEGRATION = Path(os.environ['REENRICH_INTEGRATION_ROOT'])
CACHE = Path(os.environ['REENRICH_PROCESSOR_CACHE'])
# Donor: a retained extracted source package (pdf-source-package-v1 tree)
# whose manifest first document supplies a real retained PDF. Provided by
# the operator; no instance paths are hardcoded here.
DONOR = Path(os.environ['PORTABLE_ARTICLES_DONOR'])
DONOR_DOC = json.loads((DONOR / 'manifest.json').read_text())['documents'][0]
# The manuscript source is the donor run's own retained PDF, so replayed
# donor responses bind to the same physical pages.
SOURCE_PDF = DONOR / DONOR_DOC['raw']


class SelectiveIntegration(unittest.TestCase):
    def test_selected_elements_reach_v7_request_preparation(self):
        os.environ.update(PYTHONDONTWRITEBYTECODE='1', PDF_SOURCE_PACKAGE_OFFLINE='1',
                          PDF_ENRICHMENT_OFFLINE='1', HF_HUB_OFFLINE='1',
                          TRANSFORMERS_OFFLINE='1')
        # trusted deployment bootstrap (same entry as the retained parent fixtures)
        self.assertTrue((INTEGRATION / 'entry.py').is_file())
        sys.path[:0] = [str(INTEGRATION), str(SCRIPTS),
                        str(INTEGRATION.parent / 'enrichment' / 'package'), str(METHOD)]
        from entry import bootstrap
        bootstrap(INTEGRATION.parent / 'enrichment' / 'package', SCRIPTS, METHOD)
        from qualified_enrichment import runtime
        from pdf_enrichment.package_io import SourcePackage
        from pdf_enrichment.io import sha
        import portable_articles as pa

        with tempfile.TemporaryDirectory(prefix='sel-v7-', dir=ROOT) as tmp:
            base = Path(tmp)
            # -- build real retention from the donor PDF (same as parent fixture)
            source = base / 'source.pdf'
            source.write_bytes(SOURCE_PDF.read_bytes())
            body = base / 'body.txt'
            body.write_text('Synthetic body fixture; not scientific evidence.')
            article = dict(slug='selective-fixture', title='Selective fixture',
                           doi=None, pmid=None, version='offline-fixture')
            acq = dict(
                schema='acquired-sources-v1', article=article,
                files=[dict(id='main', path=str(source), sha256=sha(source),
                            filename='source.pdf', role='manuscript', format='pdf',
                            source_url='https://example.invalid/fixture',
                            discovery_url='https://example.invalid/fixture',
                            article_slug=article['slug'],
                            identity_verification=dict(
                                status='operator-verified',
                                basis='Explicit synthetic fixture identity.')),
                       dict(id='body', path=str(body), sha256=sha(body),
                            filename='body.txt', role='body', format='other',
                            source_url='https://example.invalid/fixture',
                            discovery_url='https://example.invalid/fixture',
                            article_slug=article['slug'],
                            identity_verification=dict(
                                status='operator-verified',
                                basis='Explicit synthetic fixture identity.'))],
                attempts=[],
                obligations=dict(
                    body=dict(status='retrieved', file_ids=['body']),
                    manuscript=dict(status='retrieved', file_ids=['main'])),
                attachments=dict(status='none-listed',
                                 inspected_url='https://example.invalid/fixture',
                                 items=[]))
            (base / 'acquired.json').write_text(json.dumps(acq, indent=2))
            result = subprocess.run(
                [sys.executable, '-B', str(SCRIPTS / 'source_package.py'), 'prepare',
                 '--input', str(base / 'acquired.json'),
                 '--output', str(base / 'retention'),
                 '--application-endpoint', 'https://example.invalid/v1/chat/completions',
                 '--max-application-posts', '120'],
                cwd=str(base), capture_output=True, text=True, timeout=600)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

            # -- real workflow prepare (offline fixture) for the retention scope
            package = base / 'package'
            (base / 'attempts').mkdir()
            attempt = base / 'attempts' / 'prepare'
            result = subprocess.run(
                [sys.executable, '-B', '-m', 'pdf_source_package.launcher', 'prepare',
                 '--scope', str(base / 'retention' / 'scope.json'),
                 '--output', str(package),
                 '--attempt-dir', str(attempt), '--offline', '--offline-fixture'],
                cwd=str(METHOD), capture_output=True, text=True, timeout=1200)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

            # -- run the three phases with donor replayed responses (offline)
            from pdf_source_package import workflow, gates, execution
            doc = json.loads((package / 'manifest.json').read_text())['documents'][0]
            donor_manifest = json.loads((DONOR / 'manifest.json').read_text())
            donor_doc_id = donor_manifest['documents'][0]['identity']
            for phase in ('initial', 'classification', 'association'):
                if phase != 'initial':
                    workflow.prepare_stage(package, phase)
                gates.count_phase(package, phase, CACHE)
                approval = gates.seal(package, phase)
                approval.update(approved=True,
                                approved_by='SELECTIVE INTEGRATION OFFLINE FIXTURE ONLY',
                                source_and_candidates_reviewed=True,
                                payload_counts_reviewed=True,
                                current_route_reviewed=True)
                ap = base / f'{phase}-approval.json'
                ap.write_text(json.dumps(approval, indent=2))
                oldrows = [r for r in json.loads(
                    (DONOR / f'{phase}-plan.json').read_text())['requests']
                    if r['document'] == donor_doc_id]

                class FixtureTransport:
                    origin = 'synthetic-offline-test'

                    def __call__(self, payload, row):
                        old = next(r for r in oldrows
                                   if r['channel'] == row['channel'] and r['page'] == row['page'])
                        raw = (DONOR / old['directory'] / 'response-body.json').read_bytes()
                        if phase == 'association':
                            envelope = json.loads(raw)
                            value = json.loads(envelope['choices'][0]['message']['content'])

                            def rebind(v):
                                if isinstance(v, dict):
                                    return {k: rebind(x) for k, x in v.items()}
                                if isinstance(v, list):
                                    return [rebind(x) for x in v]
                                if isinstance(v, str) and v.startswith(donor_doc_id):
                                    return doc['identity'] + v[len(donor_doc_id):]
                                return v
                            envelope['choices'][0]['message']['content'] = json.dumps(rebind(value))
                            raw = json.dumps(envelope).encode()
                        return dict(http_status=200, raw=raw)

                rc = execution.run_phase(package, phase, ap, transport=FixtureTransport())
                self.assertEqual(rc, 0, phase)

            # -- v1 handoff via the public adapter CLI (test-only root)
            summary_attempt = base / 'attempts' / 'summary'
            result = subprocess.run(
                [sys.executable, '-B', '-m', 'pdf_source_package.launcher', 'summary',
                 '--package-dir', str(package), '--output-dir', str(base / 'summary'),
                 '--attempt-dir', str(summary_attempt), '--offline'],
                cwd=str(METHOD), capture_output=True, text=True, timeout=1200)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            result = subprocess.run(
                [sys.executable, '-B', str(SCRIPTS / 'source_package.py'), 'handoff',
                 '--retention', str(base / 'retention' / 'retention.json'),
                 '--package', str(package),
                 '--launcher-result', str(summary_attempt / 'result.json'),
                 '--method', str(METHOD), '--test-only-root', str(ROOT),
                 '--output', str(base / 'v1')],
                cwd=str(base), capture_output=True, text=True, timeout=600)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

            # -- THE SELECTIVE PATH: runtime.prepare with a selected subset
            pkg = SourcePackage(package, method=METHOD)
            eligible = [r['element_id'] for r in pkg.eligible_elements(['figure', 'table'])
                        if r['kind']]
            self.assertGreaterEqual(len(eligible), 2,
                                    'need at least 2 eligible elements to select a subset')
            selected = eligible[:1]  # strict subset
            selection = runtime.prepare(str(base / 'v1' / 'handoff.json'),
                                        str(base / 'job'), METHOD, test_root=str(ROOT))
            self.assertEqual(selection['schema'], 'qualified-selection-v1')
            self.assertEqual(selection['selected'], eligible)  # default = full roster

            # now the selective variant: prepare again with explicit subset
            job2 = base / 'job-selected'
            from pdf_enrichment import requests as v7_requests
            plan2 = v7_requests.prepare(str(package), str(job2 / 'v7'),
                                        kinds=['figure', 'table'], element_ids=selected,
                                        method=METHOD, fixture=True)
            self.assertEqual(plan2['selection'], selected)
            prepared = [r for r in plan2['requests'] if r.get('id')]
            self.assertEqual({r['element_id'] for r in prepared}, set(selected))
            # not-selected elements are explicitly recorded, not silently dropped
            skipped = [r for r in plan2['requests'] if not r.get('id')]
            self.assertTrue(skipped)
            self.assertTrue(all(r['status'] == 'not-selected' for r in skipped))
            # request evidence exists for each selected element
            for row in prepared:
                self.assertTrue((job2 / 'v7' / row['directory'] /
                                 'source-evidence.json').is_file())
                self.assertTrue((job2 / 'v7' / row['directory'] /
                                 'request-wire.json').is_file())
            # model settings surface the frozen pin, not a configurable profile
            self.assertEqual(plan2['model'], 'qwen3.8-27b')

            # New public continuation, not a requests.prepare-only endpoint.
            # Carry a real frozen review dossier through an archive and relocate
            # it before any portable enrichment preparation.
            from qualified_enrichment import reviews, exports
            prior_review = base / 'prior-review'
            reviews.create(job2 / 'v7', 'v7-run', prior_review)
            prior_export = base / 'prior-export'
            exports.export(prior_review, prior_export)
            manifest = pa.build_manifest(base / 'retention' / 'retention.json', package,
                base / 'portable', package_id='integration-01', handoff_dir=base / 'v1',
                job=job2, review=prior_review, export=prior_export, test_root=ROOT)
            self.assertIn('retention/retention.json', {f['key'] for f in manifest['files']})
            self.assertTrue(manifest['source_status']['fixture'])
            from test_article_corrections import FakeRclone
            from test_reenrich import count_and_approve, inference_double, review_and_export, candidate
            import reenrich as rr
            fake = FakeRclone()
            publication = pa.publish(base / 'portable' / 'manifest.json', 'fake', 'bucket', 'gate', runner=fake)
            # Every deleted path is explicitly owned by this TemporaryDirectory.
            import shutil
            for old in (base / 'retention', package, base / 'v1', base / 'job', job2, prior_review, prior_export, base / 'portable'):
                self.assertTrue(old.is_relative_to(base))
                shutil.rmtree(old)
            source.unlink(); body.unlink()
            restored = base / 'relocated'
            pa.restore_remote(publication['manifest_key'], publication['manifest_sha256'], restored,
                remote='fake', bucket='bucket', prefix='gate', article_key=manifest['article_key'], runner=fake)
            consumer = pa.consume(restored / 'manifest.json', selected)
            self.assertTrue(consumer['history'])
            page = base / 'synthetic-page.md'
            page.write_text('---\nkind: paper\nslug: selective-fixture\n---\n# Fixture\n\n## Results\nOld scientific prose.\n<!-- Human annotation -->\n\n## Unchanged\nHuman prose stays.\n')
            work = base / 'portable-refresh'
            rr.plan(rr.Request('selective-fixture', selected, page), manifest=restored / 'manifest.json',
                work_root=work, fixture=True, page_scope=[dict(heading='## Results', elements=selected)])
            rr.advance(work, 'prepare')
            approval = count_and_approve(work, base, cache=CACHE)
            counts = pa.load(work / 'enrichment' / 'counts.json')
            self.assertTrue(all(v['prompt_tokens'] > 0 and v['fits'] for v in counts['requests'].values()))
            rr.advance(work, 'approved-execute', approval=approval, fixture_transport=inference_double(work))
            exported = review_and_export(work, base)
            self.assertTrue(exported['inherited_history'])
            rr.candidate_import(work, candidate(work, base))
            rr.apply(work, authorize=True)
            final = rr.publish(work, 'fake', 'bucket', 'gate', runner=fake)
            self.assertEqual(final['completion'], 'offline-selected-refresh-complete')
            self.assertFalse(final['production_complete'])
            self.assertIn('Human annotation', page.read_text())
            self.assertIn('## Unchanged\nHuman prose stays.', page.read_text())

            # Full mode over the SAME real accepted source representation reaches
            # the same finished gates, with every eligible element, not the
            # selected branch's completion label.
            full_page = base / 'synthetic-full-page.md'
            full_page.write_text('---\nkind: paper\nslug: selective-fixture\n---\n# Fixture\n\n## Results\nOld scientific prose.\n<!-- Human annotation -->\n\n## Unchanged\nHuman prose stays.\n')
            full_work = base / 'portable-full-refresh'
            full_plan = rr.plan(rr.Request('selective-fixture', None, full_page), manifest=restored / 'manifest.json',
                work_root=full_work, fixture=True)
            self.assertEqual(full_plan['elements'], eligible)
            rr.advance(full_work, 'prepare')
            full_approval = count_and_approve(full_work, base, cache=CACHE)
            rr.advance(full_work, 'approved-execute', approval=full_approval, fixture_transport=inference_double(full_work))
            review_and_export(full_work, base)
            rr.candidate_import(full_work, candidate(full_work, base))
            rr.apply(full_work, authorize=True)
            full_final = rr.publish(full_work, 'fake', 'bucket', 'gate', runner=fake)
            self.assertEqual(full_final['completion'], 'offline-full-refresh-complete')
            self.assertFalse(full_final['production_complete'])
            summaries = []
            for run_root, completion in ((work, final), (full_work, full_final)):
                prepared = pa.load(run_root / 'enrichment' / 'prepared.json')
                observed_counts = pa.load(run_root / 'enrichment' / 'counts.json')
                summaries.append(dict(mode=completion['mode'], completion=completion['completion'],
                    observed_request_count=len(prepared['requests']), model=prepared['profile']['model'],
                    prompt_tokens={rid: row['prompt_tokens'] for rid, row in observed_counts['requests'].items()},
                    prepared_sha256=pa.sha(run_root / 'enrichment' / 'prepared.json'),
                    counts_sha256=pa.sha(run_root / 'enrichment' / 'counts.json'),
                    execution_sha256=pa.sha(run_root / 'enrichment' / 'execution-complete.json'),
                    export_sha256=pa.sha(run_root / 'export' / 'handoff.json'),
                    publication_manifest_sha256=pa.load(run_root / 'publication.json')['manifest_sha256'],
                    production_complete=completion['production_complete']))
            # The portable completion verifier is independent of source_package
            # v2 and of the original working roots. Keep only full restorations,
            # real synthetic pages and their git-trackable publication receipts.
            verification_inputs=[]
            for number,run_root in enumerate((work,full_work)):
                pub=pa.load(run_root/'publication.json'); saved=pa.load(run_root/'completion.json')
                destination=base/('completion-relocated-'+str(number))
                pa.restore_remote(pub['manifest_key'],pub['manifest_sha256'],destination,remote='fake',bucket='bucket',
                    prefix='gate',article_key=manifest['article_key'],runner=fake)
                original_page=page if number==0 else full_page
                relocated_page=destination/original_page.name
                shutil.copyfile(original_page,relocated_page)
                sibling=rr.page_receipt_path(original_page,saved['binding'])
                shutil.copyfile(sibling,destination/sibling.name)
                shutil.copyfile(run_root/'completion.json',destination/'completion.json')
                current_manifest=pa.load(run_root/'archive/manifest.json')
                for f in manifest['files']:
                    key=pa.object_key(manifest,'gate',f)
                    self.assertEqual(key,pa.object_key(current_manifest,'gate',f))
                    self.assertTrue(any(r['key']==key and r['reused'] for r in pub['receipts']))
                verification_inputs.append((destination,relocated_page,pub))
            for old in (work,full_work,restored):
                self.assertTrue(old.is_relative_to(base)); shutil.rmtree(old)
            verified=[]
            for destination,relocated_page,pub in verification_inputs:
                result=rr.verify_completion(destination/'completion.json',destination/'manifest.json',
                    manifest_key=pub['manifest_key'],manifest_sha256=pub['manifest_sha256'],article_key=manifest['article_key'],page=relocated_page)
                self.assertIn('Unit assignment remains uncertain',relocated_page.read_text())
                verified.append(result['completion'])
            print(json.dumps(dict(schema='portable-real-source-integration-evidence-v3', runs=summaries,
                portable_completions_verified_after_relocation=verified,shared_original_objects_verified=True,
                original_owned_roots_removed=True, paid_model_posts=0, transport='offline-inference-and-R2-doubles')), flush=True)



if __name__ == '__main__':
    unittest.main(verbosity=2)
