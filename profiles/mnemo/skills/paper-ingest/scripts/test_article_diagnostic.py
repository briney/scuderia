"""Selected diagnostic and endpoint regressions; no application network calls."""
import copy
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
import urllib.error
import urllib.request

import article_enrichment as ae
import portable_articles as pa
import reenrich as rr
from article_runtime import trusted_modules
from test_article_corrections import synthetic, FakeRclone
from test_reenrich import fixture_profile, count_and_approve, inference_double, review_and_export


class Endpoints(unittest.TestCase):
    def setUp(self):
        trusted_modules()
        self.tmp=tempfile.TemporaryDirectory(dir=os.environ['SOURCE_PACKAGE_TEST_ROOT'])
        self.addCleanup(self.tmp.cleanup); self.base=Path(self.tmp.name); self.work=self.base/'work'
        manifest,_=synthetic(self.base)
        rr.plan(rr.Request('synthetic',['main::table-1']),manifest=manifest,work_root=self.work,
                fixture=True,model_profile=fixture_profile())
        rr.advance(self.work,'prepare'); ap=count_and_approve(self.work,self.base)
        self.approval=pa.load(ap); self.prepared=pa.load(self.work/'enrichment/prepared.json')

    def test_http_and_https_explicit_approval(self):
        for endpoint in ('http://localhost:4000/v1/chat/completions','https://example.invalid/v1/chat/completions'):
            with self.subTest(endpoint=endpoint):
                ae.approval(self.work/'enrichment',self.prepared,dict(self.approval,endpoint=endpoint))

    def test_malformed_endpoints_refused(self):
        for endpoint in ('ftp://example.invalid/path','file:///path','http:///path',
                         'http://user@example.invalid/path','http://:pass@example.invalid/path',
                         'http://example.invalid/path?q=1','http://example.invalid/path#part',
                         'http://example.invalid:bad/path','http://example.invalid:70000/path',
                         'http://example.invalid:/path','http://example.invalid:0/path',
                         ' http://example.invalid/path','http://exam ple.invalid/path',
                         'http://example.invalid/pa\nth','http://example.invalid/path?',
                         'http://example.invalid/path#','http://[bad/path',None,42):
            with self.subTest(endpoint=endpoint), self.assertRaises(ValueError):
                ae.approval(self.work/'enrichment',self.prepared,dict(self.approval,endpoint=endpoint))

    def test_redirect_never_forwarded_and_response_redacted(self):
        class Redirect(urllib.request.BaseHandler):
            handler_order=100
            def __init__(self,location): self.location=location; self.calls=[]
            def http_open(self,request):
                self.calls.append(request.full_url)
                headers=__import__('email.message',fromlist=['Message']).Message()
                headers['Location']=self.location
                response=__import__('urllib.response',fromlist=['addinfourl']).addinfourl(
                    io.BytesIO(b'{"echo":"TEST_ONLY_NOT_A_CREDENTIAL"}'),headers,request.full_url,302)
                response.msg='Found'
                return response
        for location in ('http://source.invalid/redirect','http://other.invalid/redirect','https://other.invalid/redirect'):
            handler=Redirect(location)
            opener=urllib.request.build_opener(ae.NoRedirect(),urllib.request.ProxyHandler({}),handler)
            with patch.dict(os.environ,{'DIAGNOSTIC_TEST_KEY':'TEST_ONLY_NOT_A_CREDENTIAL'}), \
                 patch.object(ae.urllib.request,'build_opener',return_value=opener):
                result=ae._post(b'{}',dict(endpoint='http://source.invalid/start',credential_env='DIAGNOSTIC_TEST_KEY',timeout_seconds=1200))
            self.assertEqual(handler.calls,['http://source.invalid/start'])
            self.assertEqual(result['http_status'],302)
            self.assertNotIn(b'TEST_ONLY_NOT_A_CREDENTIAL',result['raw'])
            self.assertTrue(result['credential_echo_redacted'])


class Diagnostic(unittest.TestCase):
    def setUp(self):
        trusted_modules()
        self.tmp=tempfile.TemporaryDirectory(dir=os.environ['SOURCE_PACKAGE_TEST_ROOT'])
        self.addCleanup(self.tmp.cleanup); self.base=Path(self.tmp.name); self.work=self.base/'work'
        self.source=Path(os.environ['PORTABLE_ARTICLES_DONOR'])
        from pdf_enrichment.package_io import SourcePackage
        self.pkg=SourcePackage(self.source,method=os.environ['PDF_ENRICHMENT_METHOD'])
        self.ids=[r['element_id'] for r in self.pkg.eligible_elements(['figure','table']) if r['kind']][:1]
        self.assertTrue(self.ids)

    def ready(self):
        self.manifest=self.base/'diagnostic/manifest.json'
        self.m=pa.build_diagnostic(self.source,self.manifest.parent,elements=self.ids)
        rr.diagnostic_plan(self.manifest,self.ids,work_root=self.work,model_profile=fixture_profile())
        return rr.advance(self.work,'prepare')

    def test_real_saved_source_preparation_without_production_claim(self):
        before=pa.tree(self.source)
        v=self.ready()
        self.assertFalse(v['fixture']); self.assertEqual(v['scope'],'selected-diagnostic')
        self.assertEqual(v['roster'],self.ids); self.assertEqual(len(v['requests']),len(self.ids))
        self.assertIsNone(self.m['article']); self.assertIsNone(self.m['article_key'])
        self.assertFalse(self.m['source_status']['complete'])
        self.assertFalse(self.m['source_status']['acquisition_verified'])
        row=v['requests'][0]; e=self.m['elements'][0]
        self.assertEqual(row['source_sha256'],self.pkg.doc(e['document'])['sha256'])
        wire=pa.load(self.work/'enrichment'/row['directory']/'request-wire.json')
        self.assertIn('Surrounding native page context',json.dumps(wire))
        self.assertTrue(e['evidence']['body_fragments'])
        status=rr.execute(work_root=self.work)
        self.assertFalse(status['production_complete']); self.assertFalse(status['page_refresh_complete'])
        self.assertEqual(before,pa.tree(self.source))
        self.assertFalse((self.work/'enrichment/execution-start.json').exists())

    def test_extraction_selection_is_not_full_native_inventory(self):
        self.ready()
        original={d['identity']:d for d in self.pkg.manifest['documents']}
        for d in self.m['documents']:
            self.assertEqual(d['selected_pages'],original[d['identity']]['selected_pages'])
            self.assertEqual(d['extraction_scope'],original[d['identity']]['extraction_scope'])

    def test_explicit_roster_and_production_refusal(self):
        self.ready()
        for ids in (None,[],self.ids*2,['not-an-element']):
            with self.assertRaises(ValueError):
                rr.diagnostic_plan(self.manifest,ids,work_root=self.base/'invalid')
        with self.assertRaises(ValueError):
            rr.plan(rr.Request('invented',self.ids),manifest=self.manifest,work_root=self.base/'production')
        with self.assertRaises(ValueError): ae.prepare(self.base,'wrong',self.manifest,self.ids)
        for operation in (lambda:rr.candidate_import(self.work,self.base/'missing.json'),
                          lambda:rr.apply(self.work,authorize=True),
                          lambda:rr.publish(self.work,'fake','bucket','gate',runner=FakeRclone()),
                          lambda:pa.publish(self.manifest,'fake','bucket','gate',runner=FakeRclone())):
            with self.assertRaisesRegex(ValueError,'diagnostic'): operation()
        self.assertFalse((self.work/'archive').exists())

    def test_live_double_shared_execute_review_export_and_no_retry(self):
        self.ready(); ap=count_and_approve(self.work,self.base)
        a=pa.load(ap); self.assertEqual(a['scope'],'selected-diagnostic')
        a['endpoint']='http://example.invalid/v1/chat/completions'; ap.write_text(json.dumps(a))
        transport=inference_double(self.work); rows=iter(pa.load(self.work/'enrichment/prepared.json')['requests'])
        env={k:v for k,v in os.environ.items() if k not in ('PDF_ENRICHMENT_OFFLINE','PDF_SOURCE_PACKAGE_OFFLINE')}
        with patch.dict(os.environ,env,clear=True), patch.object(ae,'_post',side_effect=lambda payload,value:transport(payload,next(rows))) as post:
            rr.advance(self.work,'approved-execute',approval=ap,authorize=True)
            self.assertEqual(post.call_count,len(self.ids))
            rr.advance(self.work,'approved-execute',approval=ap,authorize=True)
            self.assertEqual(post.call_count,len(self.ids))
        exported=review_and_export(self.work,self.base)
        self.assertFalse(exported['fixture']); self.assertFalse(exported['production_complete'])
        self.assertEqual(exported['scope'],'selected-diagnostic')
        self.assertEqual(exported['source_status'],self.m['source_status'])
        self.assertTrue(exported['inherited_history']); self.assertIn('unreviewed_aspects',json.dumps(exported))
        status=rr.execute(work_root=self.work)
        self.assertEqual(status['completion'],'diagnostic-export-ready')
        self.assertFalse(status['production_complete']); self.assertFalse(status['page_refresh_complete'])
        self.assertIsNone(status['next_step'])

    def test_diagnostic_manifest_recomputed_not_promoted_or_relabelled(self):
        self.ready(); original=copy.deepcopy(self.m)
        for field in ('fixture','complete','kind','scope'):
            m=copy.deepcopy(original)
            if field in ('fixture','complete'): m['source_status'][field]=not m['source_status'][field]
            elif field=='kind': m['elements'][0]['kind']='table' if m['elements'][0]['kind']=='figure' else 'figure'
            else: m['scope']='production'
            self.manifest.write_text(json.dumps(m))
            mapping=pa.load(self.manifest.parent/'local-map.json'); mapping['manifest_sha256']=pa.sha(self.manifest)
            (self.manifest.parent/'local-map.json').write_text(json.dumps(mapping))
            with self.assertRaises(ValueError): pa.verify_source(self.manifest)

    def test_timeout_reserves_once_without_response_or_retry(self):
        self.ready(); ap=count_and_approve(self.work,self.base)
        env={k:v for k,v in os.environ.items() if k not in ('PDF_ENRICHMENT_OFFLINE','PDF_SOURCE_PACKAGE_OFFLINE')}
        with patch.dict(os.environ,env,clear=True), patch.object(ae,'_post',side_effect=TimeoutError('test timeout')) as post:
            rr.advance(self.work,'approved-execute',approval=ap,authorize=True)
            rr.advance(self.work,'approved-execute',approval=ap,authorize=True)
            self.assertEqual(post.call_count,1)
        state=rr.execute(work_root=self.work)['stage_receipts']['enrichment']['accounting']
        self.assertEqual(state['counts']['uncertain'],1)
        self.assertTrue((self.work/'enrichment/requests/r000001/reservation.json').exists())
        self.assertFalse((self.work/'enrichment/execution-complete.json').exists())
        self.assertFalse((self.work/'export').exists())

    def test_approval_scope_tampering_and_fixture_run_promotion_refused(self):
        self.manifest=self.base/'diagnostic/manifest.json'
        pa.build_diagnostic(self.source,self.manifest.parent,elements=self.ids)
        rr.diagnostic_plan(self.manifest,self.ids,work_root=self.work,fixture=True,model_profile=fixture_profile())
        rr.advance(self.work,'prepare'); ap=count_and_approve(self.work,self.base)
        original=pa.load(ap)
        for field,value in (('scope','production'),('production_complete',True),('page_refresh_complete',True),('maximum_posts',0)):
            a=dict(original); a[field]=value; ap.write_text(json.dumps(a))
            with self.assertRaises(ValueError): rr.advance(self.work,'approved-execute',approval=ap,fixture_transport=inference_double(self.work))
        ap.write_text(json.dumps(original))
        with self.assertRaisesRegex(ValueError,'fixture'): rr.advance(self.work,'approved-execute',approval=ap,authorize=True)
        self.assertFalse((self.work/'enrichment/execution-start.json').exists())

    def test_diagnostic_payload_and_source_tamper_refused(self):
        self.ready(); row=pa.load(self.work/'enrichment/prepared.json')['requests'][0]
        wire=self.work/'enrichment'/row['directory']/'request-wire.json'
        wire.write_text(wire.read_text()+' ')
        with self.assertRaises(ValueError): rr.advance(self.work,'count')
        # Only owned scratch copies are changed, never the donor.
        import shutil
        clone=self.base/'source-copy'; shutil.copytree(self.source,clone)
        m=pa.build_diagnostic(clone,self.base/'copy-manifest',elements=self.ids)
        native=m['elements'][0]['context']['native_text_keys'][0].removeprefix('package/')
        (clone/native).write_text('[]')
        with self.assertRaisesRegex(ValueError,'corrupt-archive-source'): pa.verify_source(self.base/'copy-manifest/manifest.json')

    def test_live_table_double_preserves_real_table_type(self):
        source=os.environ.get('DIAGNOSTIC_TABLE_DONOR')
        if not source: self.skipTest('explicit saved table donor not supplied')
        from pdf_enrichment.package_io import SourcePackage
        self.source=Path(source); self.pkg=SourcePackage(self.source,method=os.environ['PDF_ENRICHMENT_METHOD'])
        self.ids=[r['element_id'] for r in self.pkg.eligible_elements(['table']) if r['kind']=='table'][:1]
        self.assertTrue(self.ids); self.test_live_double_shared_execute_review_export_and_no_retry()
        self.assertEqual(pa.load(self.work/'enrichment/prepared.json')['requests'][0]['kind'],'table')
        ev=pa.load(self.work/'enrichment/requests/r000001/source-evidence.json')
        docs=[d['detail']['document'] for d in ev['diagnostic_context']['dispositions'] if d['kind']=='source-document']
        self.assertEqual(docs,[ev['source_document']])
        self.assertIn('diagnostic-only',ev['diagnostic_context']['source_status']['holds'])
        history=pa.prompt_history(pa.verify_local(self.manifest)[1],self.m['elements'][0]['inherited'],self.m['elements'][0])
        self.assertTrue(history)
        self.assertTrue(all(h['qualifications'] for h in history))
        text=json.dumps(history)
        for d in self.m['documents']:
            if d['identity']!=ev['source_document']: self.assertNotIn(d['source_sha256'],text)

    def test_cli_diagnostic_plan_prepare_and_scope_errors(self):
        command=[sys.executable,'-B',str(Path(pa.__file__)),'diagnostic-manifest','--package',str(self.source),
                 '--output',str(self.base/'cli-source'),'--element',self.ids[0]]
        result=subprocess.run(command,cwd=self.base,capture_output=True,text=True,timeout=120)
        self.assertEqual(result.returncode,0,result.stderr)
        command=[sys.executable,'-B',str(Path(rr.__file__)),'diagnostic-plan','--manifest',str(self.base/'cli-source/manifest.json'),
                 '--work-root',str(self.work)]
        result=subprocess.run(command,cwd=self.base,capture_output=True,text=True,timeout=120)
        self.assertEqual(result.returncode,2)
        result=subprocess.run(command+['--element',self.ids[0]],cwd=self.base,capture_output=True,text=True,timeout=120)
        self.assertEqual(result.returncode,0,result.stderr)
        for operation in ('prepare','execute'):
            result=subprocess.run([sys.executable,'-B',str(Path(rr.__file__)),operation,'--work-root',str(self.work)],
                                  cwd=self.base,capture_output=True,text=True,timeout=120)
            self.assertEqual(result.returncode,0,result.stderr)
        result=subprocess.run(command+['--element',self.ids[0],'--page','forbidden.md'],cwd=self.base,capture_output=True,text=True,timeout=120)
        self.assertEqual(result.returncode,2)


if __name__=='__main__': unittest.main(verbosity=2)
