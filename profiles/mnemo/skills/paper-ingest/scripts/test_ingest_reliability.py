"""Synthetic regressions for deployment and operator reliability; no model calls."""
import copy
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import article_enrichment as ae
import portable_articles as pa
from pdf_enrichment.requests import native_line
from test_article_corrections import synthetic, FakeRclone


class ProjectionTests(unittest.TestCase):
    def test_context_keeps_reused_page_ids_and_changed_text(self):
        with tempfile.TemporaryDirectory(dir=os.environ['SOURCE_PACKAGE_TEST_ROOT']) as tmp:
            root=Path(tmp); manifest,m=synthetic(root)
            _,paths=pa.verify_local(manifest)
            element=m['elements'][0]
            element['evidence']['body_fragments'][0]['native_lines']=[
                dict(line_id='local-1',page=1,text='007',bbox=[0,0,1,1])]
            lines=[dict(id='local-1',page=1,text='007',bbox=[0,0,1,1]),
                   dict(id='local-1',page=2,text='007',bbox=[0,0,1,1]),
                   dict(id='local-1',page=1,text='different',bbox=[0,0,1,1]),
                   dict(id='local-1',text='007',bbox=[0,0,1,1])]
            path=root/'context.json'; path.write_text(json.dumps(lines))
            paths['context']=path; element['context']['native_text_keys']=['context']
            wire,_,_=ae.wire_for(element,paths,ae.DEFAULT_PROFILE)
            content=next(c['text'] for c in wire['messages'][0]['content'] if c.get('text','').startswith('Surrounding'))
            self.assertIn('\n[',content)
            remaining=json.loads(content.split('\n',1)[1])
            self.assertEqual([r['text'] for r in remaining],['007','different','007'])

    def test_native_projection_preserves_unicode_offsets_and_original(self):
        line=dict(id='line',text='007 ± 𝛼',bbox=[0,0,2,2],spans=[dict(text='007 ',font='A'),dict(text='± 𝛼',font='B')])
        original=copy.deepcopy(line); result=native_line(line,2)
        self.assertEqual(line,original)
        self.assertEqual([(s['start'],s['end']) for s in result['spans']],[(0,4),(4,7)])
        self.assertEqual(''.join(s['text'] for s in result['spans']),line['text'])
        self.assertNotIn('font',result['spans'][0])
        bad=native_line(dict(line,text='mismatch'),2)
        self.assertFalse(bad['span_offsets_exact'])
        self.assertTrue(all(s['start'] is None and s['end'] is None for s in bad['spans']))

    def test_table_contract_accepts_anchor_arrays_and_rejects_covered_slots(self):
        from test_reenrich import response_content
        from pdf_enrichment import tables
        evidence=dict(element_id='table',body_fragments=[dict(fragment_id='body',page=1,crop='crop',native_lines=[])],captions=[])
        value=response_content(dict(kind='table'),evidence)
        value['rows'].append(dict(index=1,span_from=None,span_to=None))
        value['columns'].append(dict(index=1,span_from=None,span_to=None))
        cell=value['cells'][0]; cell['col_span']=2
        value['cells'] += [dict(cell,row=1,column=i,col_span=1) for i in (0,1)]
        value['header_hierarchy']={'1,0':['0,0'],'1,1':['0,0']}
        value['notation_coverage']={'status':'unknown'}
        self.assertEqual(tables.assemble(evidence,value)['header_hierarchy'],value['header_hierarchy'])
        for bad in ('0,0',['0,1']):
            changed=copy.deepcopy(value); changed['header_hierarchy']['1,1']=bad
            with self.assertRaises(ValueError): tables.assemble(evidence,changed)
        value['notation_coverage']='all-cells-checked'
        with self.assertRaises(ValueError): tables.assemble(evidence,value)


class PathTests(unittest.TestCase):
    def test_offline_archive_transport_never_starts_rclone(self):
        with patch.dict(os.environ,PDF_ENRICHMENT_OFFLINE='1'),patch.object(pa.subprocess,'run') as run:
            with self.assertRaisesRegex(ValueError,'offline-rclone-forbidden'): pa._run_rclone(['rclone','lsf','test:bucket'])
            run.assert_not_called()

    def test_internal_upload_and_readback_accept_system_temp_alias(self):
        with tempfile.TemporaryDirectory(dir=os.environ['SOURCE_PACKAGE_TEST_ROOT']) as tmp:
            root=Path(tmp); actual=root/'real'; actual.mkdir(); alias=root/'alias'; alias.symlink_to(actual,target_is_directory=True)
            source=root/'source'; source.write_bytes(b'original')
            fake=FakeRclone(); transport=pa.RcloneTransport('fake','bucket',runner=fake)
            with patch.object(tempfile,'tempdir',str(alias)):
                result=transport.upload(source,'object',pa.sha(source),source.stat().st_size)
                self.assertEqual(result['method'],'read_back_sha256')
                self.assertTrue(transport.upload(source,'object',pa.sha(source),source.stat().st_size)['reused'])
            self.assertEqual(list(actual.iterdir()),[])

    def test_external_symlink_diagnostic_names_component(self):
        from article_runtime import absolute
        with tempfile.TemporaryDirectory(dir=os.environ['SOURCE_PACKAGE_TEST_ROOT']) as tmp:
            root=Path(tmp); real=root/'real'; real.mkdir(); alias=root/'alias'; alias.symlink_to(real,target_is_directory=True)
            with self.assertRaisesRegex(ValueError,'symlink-forbidden:.*alias'):
                absolute(alias/'source')
            source=real/'source'; source.write_text('x'); os.link(source,real/'hardlink')
            with self.assertRaisesRegex(ValueError,'regular-single-link-file-required'): absolute(source)

    def test_manifest_limit_explains_size_and_path(self):
        with tempfile.TemporaryDirectory(dir=os.environ['SOURCE_PACKAGE_TEST_ROOT']) as tmp:
            path=Path(tmp)/'too-large.json'; path.write_text('{"data":123}')
            with patch.object(pa,'MAX_MANIFEST_BYTES',8):
                with self.assertRaisesRegex(ValueError,'json-size-limit:.*too-large.json.*8'):
                    pa.load(path)


class RouteTests(unittest.TestCase):
    def test_routes_existing_legacy_and_packaged_pages_to_refresh(self):
        import reenrich as rr
        with tempfile.TemporaryDirectory(dir=os.environ['SOURCE_PACKAGE_TEST_ROOT']) as tmp:
            root=Path(tmp); manifest,m=synthetic(root)
            page=root/'paper.md'; page.write_text('---\nkind: paper\nslug: synthetic\n---\n# Synthetic\n')
            legacy=rr.route('synthetic',page=page,work_root=root/'legacy')
            self.assertEqual(legacy['route'],'legacy-refresh')
            self.assertEqual(legacy['completion_verifier'],'reenrich.verify_completion')
            self.assertEqual(legacy['next_step'],'adopt')
            packaged=rr.route('synthetic',page=page,manifest=manifest,work_root=root/'packaged',fixture=True)
            self.assertEqual(packaged['route'],'full-refresh')
            self.assertEqual(packaged['next_step'],'prepare')
            page.write_text(page.read_text()+'Changed by human\n')
            with self.assertRaisesRegex(ValueError,'page-changed'): rr.execute(work_root=root/'legacy')

    def test_new_route_cannot_be_selected_refresh(self):
        import reenrich as rr
        with tempfile.TemporaryDirectory(dir=os.environ['SOURCE_PACKAGE_TEST_ROOT']) as tmp:
            root=Path(tmp); page=root/'new.md'
            result=rr.route('synthetic',page=page,work_root=root/'new')
            self.assertEqual(result['route'],'initial-ingest')
            self.assertEqual(result['completion_verifier'],'final_products.verify_ingest')
            self.assertFalse(result['production_complete'])
            with self.assertRaisesRegex(ValueError,'selected-refresh-requires-existing-page'):
                rr.route('synthetic',page=page,work_root=root/'selected',elements=['table'])


class OperatorTests(unittest.TestCase):
    def test_native_article_route_and_status_return_exact_continuation(self):
        import sys
        from qualified_enrichment.launcher import Deployment,launch
        scripts=Path(ae.__file__).parent
        with tempfile.TemporaryDirectory(dir=os.environ['SOURCE_PACKAGE_TEST_ROOT']) as tmp:
            root=Path(tmp); page=root/'paper.md'; page.write_text('---\nkind: paper\nslug: synthetic\n---\n# Synthetic\n')
            args=dict(operation='article',arguments=dict(command='route',article='synthetic',page=str(page),work_root=str(root/'work')),
                      attempt_dir=str(root/'attempt'),offline=True)
            result=launch(args,Deployment(scripts,scripts,scripts,scripts,Path(sys.executable)))
            self.assertTrue(result['success'],result)
            value=json.loads((root/'attempt/operation-result.json').read_text())
            self.assertEqual(value['next_operation']['arguments']['command'],'adopt')
            self.assertEqual(value['next_operation']['missing_inputs'],['manifest','identity_approval'])
            self.assertEqual(value['completion_verifier'],'reenrich.verify_completion')

    def test_status_advances_to_export_after_review(self):
        import reenrich as rr
        from test_reenrich import fixture_profile,count_and_approve,inference_double,review_and_export
        with tempfile.TemporaryDirectory(dir=os.environ['SOURCE_PACKAGE_TEST_ROOT']) as tmp:
            root=Path(tmp); manifest,m=synthetic(root); work=root/'work'
            rr.plan(rr.Request('synthetic'),manifest=manifest,work_root=work,fixture=True,model_profile=fixture_profile())
            rr.advance(work,'prepare'); ap=count_and_approve(work,root)
            rr.advance(work,'approved-execute',approval=ap,fixture_transport=inference_double(work))
            with patch.object(ae,'export',return_value={}):
                # Author/import the real review using existing fixture helper, but don't export yet.
                with self.assertRaises(FileNotFoundError): review_and_export(work,root)
            status=rr.execute(work_root=work)
            self.assertEqual(status['next_step'],'export')
            self.assertEqual(status['next_operation']['missing_inputs'],[])


class PacketTests(unittest.TestCase):
    def test_batches_bind_current_ids_and_report_oversized_elements(self):
        from qualified_enrichment import reviews
        dossier=dict(schema='portable-review-dossier-v3',policy='observed-limitations-v1',
                     snapshot=dict(source_package='synthetic',source_files=[],elements=[]))
        # Reuse production packet construction with minimal unresolved outcomes.
        for i in range(3):
            dossier['snapshot']['elements'].append(dict(element_id=str(i),source_sha256='0'*64,
                outcome=dict(status='failed',reason='x'*(10000 if i==2 else 400)),evidence={},source_element={}))
        result=reviews.packet_batches(dossier,'0'*64,max_bytes=2500)
        self.assertEqual(result['oversized'],['2'])
        self.assertEqual([e['element_id'] for p in result['packets'] for e in p['elements']],['0','1'])
        self.assertTrue(all(len(json.dumps(p,ensure_ascii=False,indent=2).encode())+1<=2500 for p in result['packets']))

    def test_export_rejects_incomplete_batches_even_without_inventory(self):
        import reenrich as rr
        from qualified_enrichment import reviews
        from test_reenrich import fixture_profile,count_and_approve,inference_double,reviewer
        from article_runtime import digest
        with tempfile.TemporaryDirectory(dir=os.environ['SOURCE_PACKAGE_TEST_ROOT']) as tmp:
            root=Path(tmp); manifest,m=synthetic(root);work=root/'work'
            rr.plan(rr.Request('synthetic'),manifest=manifest,work_root=work,fixture=True,model_profile=fixture_profile())
            rr.advance(work,'prepare');ap=count_and_approve(work,root)
            rr.advance(work,'approved-execute',approval=ap,fixture_transport=inference_double(work))
            rr.advance(work,'review-create')
            dossier=pa.load(work/'review/dossier.json'); ids=[e['element_id'] for e in dossier['snapshot']['elements']]
            self.assertGreater(len(ids),1)
            for i,eid in enumerate(ids):
                packet=reviews.packet_value(dossier,pa.sha(work/'review/dossier.json'),[eid],8000000)
                pp=root/f'packet-{i}.json';pa.save(pp,packet)
                submission=root/f'review-{i}.json';pa.save(submission,dict(schema='contextual-review-v2',packet_sha256=digest(packet),reviewer=reviewer(),findings=[],coverage=[],resolutions=[]))
                rr.advance(work,'review-import',packet=pp,submission=submission)
                if i==0:
                    (work/'review/packets.json').unlink()
                    self.assertEqual(rr.execute(work_root=work)['next_step'],'review-import')
                    with self.assertRaisesRegex(ValueError,'all-roster-elements'): rr.advance(work,'export')
                    self.assertFalse((work/'export').exists())
            self.assertEqual(rr.execute(work_root=work)['next_step'],'export')
            rr.advance(work,'export')
