"""Executable full/selective refresh tests; isolated synthetic sources and doubles."""
import copy
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

import portable_articles as pa
import reenrich as rr
import article_enrichment as ae
from article_runtime import digest, trusted_modules
from test_article_corrections import synthetic, FakeRclone


def reviewer():
    return dict(kind='human',identity='Synthetic test operator',model=None,provider=None,
                check='Offline mechanics only',timestamp='2026-01-01T00:00:00Z')


def fixture_profile():
    return dict(ae.DEFAULT_PROFILE,name='synthetic-larger-model',model='synthetic-larger-model',
                max_tokens=4096,context_limit=32768,counting='operator-exact-count-receipt')


def response_content(row,ev):
    if row['kind']=='figure':
        refs=[f['fragment_id'] for f in ev['body_fragments']]+[f['region_id'] for f in ev['captions']]
        return dict(shown={'summary':dict(text='Synthetic fixture observation only.',evidence_basis='crop-image',source_ref=refs[0])},
            observations=[],caption_context={},limitations=[],coverage=dict(scope='image-plus-caption',status='complete',source_refs=refs,gaps=[]))
    band=dict(index=0,span_from=None,span_to=None)
    cell=dict(row=0,column=0,row_span=1,col_span=1,raw_value=None,native_line_ids=[],raster_text=None,
              blank=False,unreadable=False,unresolved=True,notes='Synthetic unresolved cell',
              source_refs=[ev['body_fragments'][0]['fragment_id']])
    return dict(status='unresolved',rows=[band],columns=[band],cells=[cell],header_hierarchy={},units=[],caption_markers=[],
                unresolved=[dict(kind='units',ref='0',reason='Synthetic unresolved units; not scientific output.')])


def count_and_approve(work,base,*,cache=None):
    v=pa.load(work/'enrichment'/'prepared.json')
    if v['profile']['counting']=='operator-exact-count-receipt':
        evidence=base/(work.name+'-count-evidence.txt'); evidence.write_text('Synthetic exact-count fixture evidence; not a provider measurement.')
        count=base/(work.name+'-count.json')
        pa.save(count,dict(schema='portable-exact-count-input-v1',prepared_sha256=pa.sha(work/'enrichment'/'prepared.json'),
            model=v['profile']['model'],requests={r['id']:dict(request_sha256=r['request_sha256'],prompt_tokens=100) for r in v['requests']},
            attestation='Synthetic offline count input, cannot promote fixture',evidence=dict(path=str(evidence),sha256=pa.sha(evidence),method='provider-count-api')))
        rr.advance(work,'count',count_receipt=count)
    else: rr.advance(work,'count',cache=cache)
    a=rr.advance(work,'seal')
    a.update(approved=True,approved_by='Synthetic offline fixture',source_payload_counts_reviewed=True,
             endpoint='https://example.invalid/v1/chat/completions',credential_env='NEVER_READ_FIXTURE_KEY')
    ap=base/(work.name+'-approval.json'); pa.save(ap,a)
    return ap


def inference_double(work,*,wrong_model=False,wrong_count=False,interrupt=False):
    def transport(payload,row):
        if interrupt: raise TimeoutError('injected possibly-posted interruption')
        v=pa.load(work/'enrichment'/'prepared.json'); counts=pa.load(work/'enrichment'/'counts.json')
        ev=pa.load(work/'enrichment'/row['directory']/'source-evidence.json')
        n=counts['requests'][row['id']]['prompt_tokens']+(1 if wrong_count else 0)
        content=response_content(row,ev)
        raw=json.dumps(dict(model='wrong-route' if wrong_model else v['profile']['model'],
            choices=[dict(finish_reason='stop',message=dict(content=json.dumps(content)))],
            usage=dict(prompt_tokens=n,completion_tokens=10,total_tokens=n+10))).encode()
        return dict(http_status=200,raw=raw)
    return transport


def review_and_export(work,base):
    rr.advance(work,'review-create')
    packet_path=work/'review'/'packet.json'
    if packet_path.exists():
        packet=pa.load(packet_path)
        current=packet['schema']=='contextual-review-packet-v2'
        value=dict(schema='contextual-review-v2' if current else 'contextual-review-v1',packet_sha256=digest(packet),reviewer=reviewer(),findings=[],coverage=[],resolutions=[])
        if current:
            _,_,manifest,m,_,_,_=rr.context(work)
            source=next(f for f in m['files'] if f['key'].endswith(('page.txt','native-text.txt')))
            value['assessment']=dict(usable_evidence=True,reason='Synthetic native evidence review.',source_refs=[{k:source[k] for k in ('key','sha256')}],unattempted={})
        # Explicit new warning with source association, carried into every export.
        for e in packet['elements']:
            value['findings'].append(dict(element_id=e['element_id'],source_sha256=e['source_sha256'],target='',
                category='synthetic-known-uncertainty',reason='Unit assignment remains uncertain in the synthetic fixture.',stage='answer',evidence=[dict(pointer='/body_fragments/0',source_sha256=e['source_sha256'],kind='crop')] if current else []))
        path=base/(work.name+'-review.json'); pa.save(path,value)
        rr.advance(work,'review-import',submission=path)
    return rr.advance(work,'export')


def candidate(work,base):
    _,p,manifest,m,roster,binding,_=rr.context(work)
    exported=pa.load(work/'export'/'handoff.json'); views={v['element_id']:v for v in exported['elements']}
    text=(work/'original-page.md').read_text(); sections=rr._sections(text)
    scopes=p['page_scope'] or [dict(heading='## Results',elements=roster)]
    changes=[]
    qualification='Source uncertainty remains; this is synthetic test prose.'
    for s in scopes:
        start,end=sections[s['heading']]; before=text[start:end]
        after=before.replace('Old scientific prose.','Revised scientific prose from the supplied evidence. '+qualification)
        changes.append(dict(heading=s['heading'],old_sha256=rr.hashlib_sha(before),new_text=after,elements=s['elements'],
            evidence=[dict(element_id=e,source_sha256=views[e]['source_sha256'],target='/record',qualification=qualification) for e in s['elements']]))
    current=exported['schema']=='portable-qualified-export-v4'
    if current:
        for row in changes:
            for ref in row['evidence']: ref['kind']='enrichment'
    value=dict(schema='reenrich-page-candidate-v3' if current else 'reenrich-page-candidate-v2',binding=binding,export_sha256=pa.sha(work/'export'/'handoff.json'),
        reviewer=reviewer(),qualification=qualification,full_distillation_reviewed=True,replacements=changes)
    path=base/(work.name+'-candidate-input.json'); pa.save(path,value)
    return path


class ReenrichTests(unittest.TestCase):
    def setUp(self):
        trusted_modules()
        self.tmp=tempfile.TemporaryDirectory(dir=os.environ['SOURCE_PACKAGE_TEST_ROOT'],prefix='refresh-')
        self.addCleanup(self.tmp.cleanup); self.base=Path(self.tmp.name)
        self.manifest,self.m=synthetic(self.base)
        self.page=self.base/'page.md'
        self.page.write_text('---\nkind: paper\nslug: synthetic\n---\n# Synthetic\n\n## Results\nOld scientific prose.\n<!-- Human annotation -->\n[[preserved-link]]\n\n## Unchanged\nHuman prose stays byte-identical.\n')
        self.work=self.base/'work'
    def plan(self,selected=True,legacy=False):
        ids=['main::table-1'] if selected else None
        return rr.plan(rr.Request('synthetic',ids,self.page),manifest=None if legacy else self.manifest,
            work_root=self.work,fixture=True,model_profile=fixture_profile(),
            page_scope=[dict(heading='## Results',elements=ids or ['main::table-1','supplement::table-1'])])
    def ready(self,selected=True,legacy=False):
        p=self.plan(selected,legacy)
        if legacy:
            a=self.base/'adopt.json'; pa.save(a,dict(plan_sha256=pa.sha(self.work/'plan.json'),manifest_sha256=pa.sha(self.manifest),
                article=self.m['article'],requested_elements=p['request']['elements'],approved_by='Synthetic operator',identity_and_scope_reviewed=True))
            rr.adopt(self.work,self.manifest,identity_approval=a)
        rr.advance(self.work,'prepare'); ap=count_and_approve(self.work,self.base)
        rr.advance(self.work,'approved-execute',approval=ap,fixture_transport=inference_double(self.work))
        review_and_export(self.work,self.base)
        return p
    def no_change_candidate(self,full=False):
        cp=candidate(self.work,self.base); c=pa.load(cp)
        original=(self.work/'original-page.md').read_text()
        for row in c['replacements']:
            start,end=rr._sections(original)[row['heading']]; row['new_text']=original[start:end]
        c['reconciliation_outcome']='reviewed-no-scientific-text-change'
        c['full_distillation_reviewed']=full
        cp.write_text(json.dumps(c)); return cp

    def test_status_missing_stage_prerequisites_returns_structured_hold(self):
        import contextlib
        import io
        self.plan()
        for name in ('enrichment/counts.json','enrichment/execution-start.json','review/dossier.json',
                     'export/handoff.json','page-candidate/candidate.json'):
            with self.subTest(artifact=name):
                path=self.work/name; path.parent.mkdir(exist_ok=True); path.write_text('{}')
                try:
                    error=io.StringIO()
                    with contextlib.redirect_stderr(error):
                        self.assertEqual(rr.main(['execute','--work-root',str(self.work)]),2)
                    self.assertEqual(json.loads(error.getvalue())['status'],'hold')
                finally: path.unlink()

    def test_status_reuses_verified_evidence_only_within_one_call(self):
        from unittest.mock import patch
        self.ready(); rr.candidate_import(self.work,self.no_change_candidate())
        with patch.object(ae,'verify',wraps=ae.verify) as prepared, \
             patch.object(ae,'_response',wraps=ae._response) as outcomes:
            result=rr.execute(work_root=self.work)
            counts=dict(prepared=prepared.call_count,outcomes=outcomes.call_count)
        print('PORTABLE-STATUS-RECONSTRUCTIONS',counts)
        self.assertEqual(result['next_step'],'apply')
        self.assertEqual(counts,dict(prepared=1,outcomes=1))
        # No validated state survives to the next operation/mutation boundary.
        wire=self.work/'enrichment/requests/r000001/request-wire.json'
        wire.write_text('{}')
        for operation in (lambda: rr.execute(work_root=self.work),lambda: rr.apply(self.work,authorize=True),
                          lambda: rr.advance(self.work,'review-create')):
            with self.assertRaises(ValueError): operation()
        self.assertFalse((self.work/'apply-start.json').exists())

    def test_unchanged_selected_science_installs_verified_register(self):
        self.ready(); original=self.page.read_text()
        rr.candidate_import(self.work,self.no_change_candidate()); rr.apply(self.work,authorize=True)
        text=self.page.read_text()
        self.assertIn('Unit assignment remains uncertain',text)
        self.assertIn('Known unit uncertainty',text)
        self.assertIn('Article package:',text); self.assertIn('Annotated export:',text)
        self.assertNotIn('Unreviewed aspects:',text)
        self.assertIn('Old scientific prose.',text)
        self.assertEqual(rr.without_register(text),original)
        rr.publish(self.work,'fake','bucket','gate',runner=FakeRclone())
        pub=pa.load(self.work/'publication.json')
        receipt=rr.page_receipt_path(self.page,pa.load(self.work/'export'/'handoff.json')['binding'])
        args=dict(manifest_key=pub['manifest_key'],manifest_sha256=pub['manifest_sha256'],article_key=self.m['article_key'],page=self.page)
        verified=rr.verify_completion(receipt,self.work/'archive'/'manifest.json',**args)
        self.assertEqual(verified['completion'],'offline-selected-refresh-complete')
        self.assertEqual(verified['schema'],'portable-article-completion-v2')
        with self.assertRaises(ValueError): rr.verify_completion(receipt,self.work/'archive'/'manifest.json',**dict(args,manifest_sha256='0'*64))
        saved=self.page.read_text()
        for old in ('Unit assignment remains uncertain','Article package:','Annotated export:'):
            self.page.write_text(saved.replace(old,'STRIPPED'))
            with self.assertRaises(ValueError): rr.verify_completion(receipt,self.work/'archive'/'manifest.json',**args)
        self.page.write_text(saved)
        value=pa.load(receipt); value['publication']['manifest_key']='wrong/key'
        receipt.write_text(json.dumps(value))
        with self.assertRaises(ValueError): rr.verify_completion(receipt,self.work/'archive'/'manifest.json',**args)

    def test_compact_register_and_verified_legacy_replacement(self):
        self.ready(); cp=self.no_change_candidate(); submission=pa.load(cp)
        exported=pa.load(self.work/'export/handoff.json')
        p=pa.load(self.work/'plan.json')
        text=rr._candidate_text(self.work,p,self.manifest,exported['binding'],submission)
        self.assertNotIn('current_qualifications',text)
        self.assertNotIn('inherited_qualifications',text)
        self.assertIn('Known unit uncertainty',text)
        self.assertIn('Unit assignment remains uncertain',text)
        register=rr.read_register(text)
        self.assertEqual(register['schema'],'portable-page-qualification-register-v3')
        self.assertEqual(rr.install_register(text,register),text)
        # Verify current replacement against the archived snapshot. Genuine old
        # completions are tested from records produced by the baseline checkout.
        rr.candidate_import(self.work,cp); rr.apply(self.work,authorize=True)
        rr.publish(self.work,'fake','bucket','gate',runner=FakeRclone())
        _,paths=pa.verify_local(self.work/'archive/manifest.json')
        replacement=dict(register,operator_qualification='A later attributed qualification.')
        with self.assertRaisesRegex(ValueError,'register-archive'):
            rr.install_register(text,replacement)
        newer=rr.install_register(text,replacement,archive_paths=paths)
        self.assertEqual(rr.without_register(newer),rr.without_register(text))
        for key in (register['export_locator']['key'],register['annotated_export_locator']['key'],
                    register['source_locators'][0]['key'],'review/findings.json',
                    'refresh-'+register['binding'][:20]+'/review/dossier.json'):
            incomplete=dict(paths); del incomplete[key]
            with self.assertRaisesRegex(ValueError,'register-archive'):
                rr.install_register(text,replacement,archive_paths=incomplete)

    def test_refresh_keeps_qualifications_for_previously_cited_targets(self):
        self.ready(); cp=self.no_change_candidate(); c=pa.load(cp)
        c['qualification']='Prior operator limitation outside the element evidence.'
        c['replacements'][0]['evidence'][0]['qualification']='Prior exact-target limitation.'
        cp.write_text(json.dumps(c)); rr.candidate_import(self.work,cp); rr.apply(self.work,authorize=True)
        rr.publish(self.work,'fake','bucket','gate',runner=FakeRclone())
        prior_manifest=self.work/'archive/manifest.json'
        _,paths=pa.verify_local(prior_manifest)
        first=rr.read_register(self.page.read_text()); incomplete=dict(paths)
        del incomplete['refresh-'+first['binding'][:20]+'/page-candidate/input.json']
        with self.assertRaisesRegex(ValueError,'register-archive'):
            rr._register_archive(first,incomplete)
        self.work=self.base/'second'
        rr.plan(rr.Request('synthetic',['main::table-1','supplement::table-1'],self.page),manifest=prior_manifest,
            work_root=self.work,fixture=True,model_profile=fixture_profile(),
            page_scope=[dict(heading='## Results',elements=['main::table-1','supplement::table-1'])])
        rr.advance(self.work,'prepare'); approval=count_and_approve(self.work,self.base)
        rr.advance(self.work,'approved-execute',approval=approval,fixture_transport=inference_double(self.work))
        review_and_export(self.work,self.base)
        rr.candidate_import(self.work,self.no_change_candidate())
        register=rr.read_register((self.work/'page-candidate/page-candidate.md').read_text())
        self.assertEqual({t['element_id'] for t in register['selected_targets']},{'main::table-1','supplement::table-1'})
        self.assertIn('Prior operator limitation outside the element evidence.',rr.register_text(register))
        self.assertIn('Prior exact-target limitation.',rr.register_text(register))
        rr.apply(self.work,authorize=True); rr.publish(self.work,'fake','bucket','gate',runner=FakeRclone())

    def test_compact_register_preserves_warning_bearing_coverage(self):
        warning=self.base/'source/findings.json'
        warning.write_text(json.dumps(dict(coverage=dict(status='partial',gaps=['Lower panel unreadable']))))
        self.m['files'][-1]=pa.file_record('enrichment-review','review/findings.json',warning)
        self.manifest.write_text(json.dumps(self.m))
        mapping=pa.load(self.manifest.parent/'local-map.json'); mapping['manifest_sha256']=pa.sha(self.manifest)
        (self.manifest.parent/'local-map.json').write_text(json.dumps(mapping))
        self.ready(); rr.candidate_import(self.work,self.no_change_candidate())
        text=(self.work/'page-candidate/page-candidate.md').read_text()
        visible=text.split('<!-- portable-page-qualification-register-v2:')[0]
        self.assertIn('Lower panel unreadable',visible)

    def test_compact_rendering_cannot_add_page_sections(self):
        self.ready(); cp=self.no_change_candidate(); submission=pa.load(cp)
        submission['qualification']='First line.\n## Injected heading\nStill a qualification.'
        cp.write_text(json.dumps(submission)); rr.candidate_import(self.work,cp)
        text=(self.work/'page-candidate/page-candidate.md').read_text()
        self.assertEqual(set(rr._sections(text)),set(rr._sections(self.page.read_text())))
        register=rr.read_register(text)
        self.assertEqual(register['operator_qualification'],submission['qualification'])
        self.assertNotIn('## Injected heading',rr._sections(text))

    def test_compact_history_keeps_distinct_metadata_pointers(self):
        warning=self.base/'source/findings.json'
        warning.write_text(json.dumps(dict(first=dict(warning='Identical warning'),second=dict(warning='Identical warning'))))
        self.m['files'][-1]=pa.file_record('enrichment-review','review/findings.json',warning)
        self.manifest.write_text(json.dumps(self.m))
        mapping=pa.load(self.manifest.parent/'local-map.json'); mapping['manifest_sha256']=pa.sha(self.manifest)
        (self.manifest.parent/'local-map.json').write_text(json.dumps(mapping))
        self.ready(); rr.candidate_import(self.work,self.no_change_candidate())
        register=rr.read_register((self.work/'page-candidate/page-candidate.md').read_text())
        rows=[q for q in register['qualifications'] if q.get('metadata')=='Identical warning']
        self.assertEqual(len(rows),2)
        self.assertEqual({q['metadata_target'] for q in rows},{'/first/warning','/second/warning'})

    def test_page_warnings_use_recorded_source_element_and_target_scope(self):
        warning=self.base/'source/findings.json'
        main=self.m['elements'][0]; other=self.m['elements'][1]
        rows=[dict(element_id=main['element_id'],source_sha256=main['source_sha256'],target='/record/cells/0/raw_value',
                   reason='Applicable inherited warning'),
              dict(element_id=other['element_id'],source_sha256=other['source_sha256'],target='',reason='Other document warning'),
              dict(element_id=main['element_id'],source_sha256=main['source_sha256'],target='/record/units',reason='Sibling target warning'),
              dict(element_id=main['element_id'],source_sha256='0'*64,target='',reason='Different source version warning')]
        warning.write_text(json.dumps(dict(findings=rows,notice='Unscoped warning stays')))
        self.m['files'][-1]=pa.file_record('enrichment-review','review/findings.json',warning)
        self.manifest.write_text(json.dumps(self.m))
        mapping=pa.load(self.manifest.parent/'local-map.json'); mapping['manifest_sha256']=pa.sha(self.manifest)
        (self.manifest.parent/'local-map.json').write_text(json.dumps(mapping))
        self.ready(); cp=self.no_change_candidate(); submission=pa.load(cp)
        submission['replacements'][0]['evidence'][0]['target']='/record/cells/0/raw_value'
        cp.write_text(json.dumps(submission)); rr.candidate_import(self.work,cp)
        text=(self.work/'page-candidate/page-candidate.md').read_text()
        self.assertIn('Applicable inherited warning',text); self.assertIn('Unscoped warning stays',text)
        for absent in ('Other document warning','Sibling target warning','Different source version warning'):
            self.assertNotIn(absent,text)

    def test_unchanged_full_and_legacy_require_review(self):
        self.ready(selected=False,legacy=True); cp=self.no_change_candidate()
        with self.assertRaisesRegex(ValueError,'full-distillation'): rr.candidate_import(self.work,cp)
        c=pa.load(cp); c['full_distillation_reviewed']=True; cp.write_text(json.dumps(c))
        rr.candidate_import(self.work,cp); rr.apply(self.work,authorize=True)
        self.assertIn('Old scientific prose.',self.page.read_text())
        result=rr.publish(self.work,'fake','bucket','gate',runner=FakeRclone())
        self.assertEqual(result['completion'],'offline-full-refresh-complete')

    def test_unattested_unchanged_or_comment_only_still_rejected(self):
        self.ready(); cp=self.no_change_candidate(); c=pa.load(cp); c.pop('reconciliation_outcome')
        cp.write_text(json.dumps(c))
        with self.assertRaisesRegex(ValueError,'unchanged'): rr.candidate_import(self.work,cp)
        c['replacements'][0]['new_text']+='<!-- UNATTESTED -->\n'; cp.write_text(json.dumps(c))
        with self.assertRaises(ValueError): rr.candidate_import(self.work,cp)

    def test_no_page_selected_and_full_archive_completion(self):
        original=self.page.read_bytes()
        for selected in (True,False):
            work=self.base/('archive-only-'+str(selected))
            rr.plan(rr.Request('synthetic',['main::table-1'] if selected else None),manifest=self.manifest,
                work_root=work,fixture=True,model_profile=fixture_profile())
            rr.advance(work,'prepare'); ap=count_and_approve(work,self.base)
            rr.advance(work,'approved-execute',approval=ap,fixture_transport=inference_double(work))
            review_and_export(work,self.base)
            self.assertEqual(rr.execute(work_root=work)['next_step'],'publish')
            result=rr.publish(work,'fake','bucket','gate',runner=FakeRclone())
            mode='selected' if selected else 'full'
            self.assertEqual(result['completion'],'offline-'+mode+'-archive-complete')
            self.assertFalse(result['page_refresh_complete'])
            pub=pa.load(work/'publication.json')
            rr.verify_completion(work/'completion.json',work/'archive'/'manifest.json',
                manifest_key=pub['manifest_key'],manifest_sha256=pub['manifest_sha256'],article_key=self.m['article_key'])
        self.assertEqual(self.page.read_bytes(),original)

    def test_successive_refresh_history_is_nonrecursive_and_relocatable(self):
        manifest=self.manifest; fake=FakeRclone(); sizes=[]; first_keys=None
        for i in range(4):
            work=self.base/('repeat-'+str(i))
            rr.plan(rr.Request('synthetic',['main::table-1']),manifest=manifest,work_root=work,fixture=True,model_profile=fixture_profile())
            rr.advance(work,'prepare')
            wire=pa.load(work/'enrichment'/'requests/r000001/request-wire.json')
            text=json.dumps(wire)
            self.assertIn('Known unit uncertainty',text)
            self.assertEqual(text.count('data:image/'),1)
            ap=count_and_approve(work,self.base)
            rr.advance(work,'approved-execute',approval=ap,fixture_transport=inference_double(work))
            value=review_and_export(work,self.base)
            self.assertIn('Known unit uncertainty',json.dumps(value))
            self.assertNotIn('data:image/',json.dumps(value))
            self.assertTrue(all('content' not in x for x in value['inherited_history']))
            sizes.append(len(json.dumps(value['inherited_history'])))
            rr.publish(work,'fake','bucket','gate',runner=fake)
            pub=pa.load(work/'publication.json'); out=self.base/('restored-'+str(i))
            pa.restore_remote(pub['manifest_key'],pub['manifest_sha256'],out,remote='fake',bucket='bucket',prefix='gate',article_key=self.m['article_key'],runner=fake)
            manifest=out/'manifest.json'; m,paths=pa.verify_local(manifest)
            if first_keys is None: first_keys={k:pa.sha(v) for k,v in paths.items()}
            self.assertTrue(all(k in paths and pa.sha(paths[k])==h for k,h in first_keys.items()))
            shutil.rmtree(work)
        # Fixed per-refresh metadata adds linearly; no nested prior handoff bodies.
        self.assertLess(sizes[3]-sizes[2],2*(sizes[2]-sizes[1]))
        print('SUCCESSIVE-HISTORY-BYTES '+json.dumps(sizes))

    def test_completion_verifier_after_relocation_and_missing_sidecar(self):
        raw_pointer='Source PDF: papers/'+'a'*64+'.pdf\n'
        self.page.write_text(self.page.read_text().replace('<!-- Human annotation -->',raw_pointer+'<!-- Human annotation -->'))
        self.ready(); rr.candidate_import(self.work,candidate(self.work,self.base)); rr.apply(self.work,authorize=True)
        self.assertIn(raw_pointer,self.page.read_text())
        fake=FakeRclone(); rr.publish(self.work,'fake','bucket','gate',runner=fake)
        pub=pa.load(self.work/'publication.json'); out=self.base/'relocated-complete'
        pa.restore_remote(pub['manifest_key'],pub['manifest_sha256'],out,remote='fake',bucket='bucket',prefix='gate',article_key=self.m['article_key'],runner=fake)
        page=out/'page.md'; shutil.copyfile(self.page,page)
        binding=pa.load(self.work/'export/handoff.json')['binding']
        sidecar=rr.page_receipt_path(page,binding); shutil.copyfile(rr.page_receipt_path(self.page,binding),sidecar)
        receipt=out/'completion.json'; shutil.copyfile(self.work/'completion.json',receipt)
        shutil.rmtree(self.work); shutil.rmtree(self.base/'source'); self.page.unlink()
        args=dict(manifest_key=pub['manifest_key'],manifest_sha256=pub['manifest_sha256'],article_key=self.m['article_key'],page=page)
        rr.verify_completion(receipt,out/'manifest.json',**args)
        cmd=[sys.executable,'-B',str(Path(rr.__file__)),'verify-completion','--receipt',str(receipt),'--manifest',str(out/'manifest.json'),
            '--manifest-key',pub['manifest_key'],'--manifest-sha256',pub['manifest_sha256'],'--article-key',self.m['article_key'],'--page',str(page)]
        result=subprocess.run(cmd,capture_output=True,text=True,timeout=60)
        self.assertEqual(result.returncode,0,result.stderr)
        sidecar.unlink()
        with self.assertRaises((ValueError,FileNotFoundError)): rr.verify_completion(receipt,out/'manifest.json',**args)

    def test_correction_attribution_is_annotation_not_original_mutation(self):
        self.plan(); rr.advance(self.work,'prepare'); ap=count_and_approve(self.work,self.base)
        rr.advance(self.work,'approved-execute',approval=ap,fixture_transport=inference_double(self.work))
        rr.advance(self.work,'review-create'); packet=pa.load(self.work/'review/packet.json'); e=packet['elements'][0]
        ref=dict(pointer='/body_fragments/0',source_sha256=e['source_sha256'],kind='crop')
        submission=dict(schema='contextual-review-v2',packet_sha256=digest(packet),reviewer=reviewer(),coverage=[],resolutions=[],
            assessment=dict(usable_evidence=True,reason='Synthetic retained evidence review.',source_refs=[dict(key='package/main/page.txt',sha256=pa.sha(self.base/'source/main-page.txt'))],unattempted={}),
            findings=[dict(element_id=e['element_id'],source_sha256=e['source_sha256'],target='/record/cells/0/raw_value',
                category='synthetic-reading',reason='Original cell needs a qualified reading.',stage='answer',evidence=[ref])])
        path=self.base/'scoped-review.json'; pa.save(path,submission); rr.advance(self.work,'review-import',submission=path)
        _,_,manifest,_,_,binding,_=rr.context(self.work)
        _,_,views=ae.review_verify(self.work,binding,manifest)
        finding=next(f for f in views[0]['findings'] if f['category']=='synthetic-reading')
        submission['findings']=[]; submission['resolutions']=[dict(finding_id=finding['id'],reason='Synthetic operator proposal only.',
            basis='source-inspection',evidence=[ref],agreement='unambiguous',proposed_value='42',aspect='content')]
        path.write_text(json.dumps(submission)); rr.advance(self.work,'review-import',submission=path)
        exported=rr.advance(self.work,'export'); original=copy.deepcopy(exported['elements'][0]['outcome'])
        rr.candidate_import(self.work,candidate(self.work,self.base)); rr.apply(self.work,authorize=True)
        import html
        text=html.unescape(self.page.read_text())
        self.assertIn('Attributed proposals',text); self.assertIn('Synthetic operator proposal only.',text)
        self.assertIn('Synthetic test operator',text); self.assertIn('"proposed_value": "42"',text)
        self.assertEqual(pa.load(self.work/'export/handoff.json')['elements'][0]['outcome'],original)
        self.assertIsNone(original['record']['cells'][0]['raw_value'])

    def test_planned_page_cannot_be_bypassed_and_publish_detects_edit(self):
        self.ready(); fake=FakeRclone()
        with self.assertRaisesRegex(ValueError,'page-apply-required'):
            rr.publish(self.work,'fake','bucket','gate',runner=fake)
        self.assertEqual(fake.calls,[])
        rr.candidate_import(self.work,candidate(self.work,self.base)); rr.apply(self.work,authorize=True)
        def concurrent(argv,**kwargs):
            if argv[1]=='copyto' and '/manifests/' in argv[3]:
                self.page.write_text(self.page.read_text()+'Human edit during archive publication.\n')
            return fake(argv,**kwargs)
        with self.assertRaisesRegex(ValueError,'page-changed'):
            rr.publish(self.work,'fake','bucket','gate',runner=concurrent)
        self.assertTrue(self.page.read_text().endswith('Human edit during archive publication.\n'))
        self.assertFalse((self.work/'completion.json').exists())

    def test_full_finished_public_path(self):
        self.ready(selected=False)
        rr.candidate_import(self.work,candidate(self.work,self.base)); rr.apply(self.work,authorize=True)
        fake=FakeRclone(); result=rr.publish(self.work,'fake','bucket','gate',runner=fake)
        self.assertEqual(result['completion'],'offline-full-refresh-complete')
        self.assertFalse(result['production_complete'])
        self.assertIn('Human annotation',self.page.read_text()); self.assertIn('[[preserved-link]]',self.page.read_text())
        self.assertTrue(self.page.read_text().startswith('---\nkind: paper\nslug: synthetic\n---\n'))
        self.assertTrue(self.page.read_text().endswith('## Unchanged\nHuman prose stays byte-identical.\n'))
        self.assertEqual(len(pa.load(self.work/'enrichment'/'prepared.json')['requests']),2)
        self.assertEqual(rr.execute(work_root=self.work)['completion'],result['completion'])
    def test_selected_finished_and_relocated_consumer(self):
        self.ready()
        rr.candidate_import(self.work,candidate(self.work,self.base)); rr.apply(self.work,authorize=True)
        fake=FakeRclone(); result=rr.publish(self.work,'fake','bucket','gate',runner=fake)
        self.assertEqual(result['completion'],'offline-selected-refresh-complete')
        pub=pa.load(self.work/'publication.json')
        target=self.base/'remote'; pa.restore_remote(pub['manifest_key'],pub['manifest_sha256'],target,remote='fake',bucket='bucket',
            prefix='gate',article_key=self.m['article_key'],elements=['main::table-1'],runner=fake)
        shutil.rmtree(self.base/'source'); shutil.rmtree(self.work)
        consumer=pa.consume(target/'manifest.json',['main::table-1'])
        self.assertIn('Unit assignment remains uncertain',json.dumps(consumer))
        new=self.base/'new-work'; rr.plan(rr.Request('synthetic',['main::table-1']),manifest=target/'manifest.json',work_root=new,
            fixture=True,model_profile=fixture_profile()); rr.advance(new,'prepare')
        self.assertEqual(pa.load(new/'enrichment'/'prepared.json')['roster'],['main::table-1'])
        approval=count_and_approve(new,self.base)
        rr.advance(new,'approved-execute',approval=approval,fixture_transport=inference_double(new))
        exported=review_and_export(new,self.base)
        self.assertIn('Unit assignment remains uncertain',json.dumps(exported['inherited_history']))
        _,_,manifest,_,_,binding,_=rr.context(new)
        with self.assertRaisesRegex(ValueError,'qualification'): ae.consumer(new,binding,manifest,'main::table-1','/record',purpose='exact')
        checked=ae.consumer(new,binding,manifest,'main::table-1','/record',purpose='exact',qualification='Units remain uncertain.')
        self.assertFalse(checked['prior_findings_automatically_resolved'])
        self.assertTrue(checked['inherited_history'])
    def test_legacy_adoption_and_finished_selection(self):
        original=self.ready(legacy=True)
        self.assertIsNone(original['manifest']); self.assertIsNone(pa.load(self.work/'plan.json')['manifest'])
        rr.candidate_import(self.work,candidate(self.work,self.base)); rr.apply(self.work,authorize=True)
        result=rr.publish(self.work,'fake','bucket','gate',runner=FakeRclone())
        self.assertEqual(result['completion'],'offline-selected-refresh-complete')
    def test_no_request_execution_never_complete(self):
        p=self.plan(); rr.advance(self.work,'prepare')
        result=rr.execute(p,work_root=self.work)
        self.assertEqual(result['completion'],'pending'); self.assertEqual(result['next_step'],'count')
    def test_tamper_unselected_but_materialized_input(self):
        p=self.plan()
        (self.base/'source'/'supplement-page.txt').write_text('changed unselected materialized source')
        with self.assertRaisesRegex(ValueError,'corrupt-archive-source'): rr.execute(p,work_root=self.work)
    def test_tamper_after_prepare(self):
        self.plan(); rr.advance(self.work,'prepare')
        (self.base/'source'/'main-caption.txt').write_text('tampered')
        with self.assertRaises(ValueError): rr.advance(self.work,'count')
    def test_tamper_plan_page_path_and_roster(self):
        p=self.plan(); altered=copy.deepcopy(p); altered['page_path']=str(self.base/'other.md')
        with self.assertRaises(ValueError): rr.execute(altered,work_root=self.work)
        altered=copy.deepcopy(p); altered['elements']=['supplement::table-1']
        with self.assertRaises(ValueError): rr.execute(altered,work_root=self.work)
    def test_request_continuation_and_partial_export(self):
        for failed in ('r000001','r000002'):
            for failure in ('timeout','http','interrupt'):
                with self.subTest(failed=failed,failure=failure):
                    work=self.base/(failed+'-'+failure)
                    rr.plan(rr.Request('synthetic'),manifest=self.manifest,work_root=work,fixture=True,model_profile=fixture_profile())
                    rr.advance(work,'prepare'); ap=count_and_approve(work,self.base)
                    calls=[]; success=inference_double(work)
                    def transport(raw,row):
                        calls.append(row['id'])
                        if row['id']==failed:
                            if failure=='timeout': raise TimeoutError('possibly sent')
                            if failure=='interrupt': raise KeyboardInterrupt()
                            return dict(http_status=500,raw=b'{"error":"synthetic failure"}')
                        return success(raw,row)
                    if failure=='interrupt':
                        with self.assertRaises(KeyboardInterrupt): rr.advance(work,'approved-execute',approval=ap,fixture_transport=transport)
                    else:
                        rr.advance(work,'approved-execute',approval=ap,fixture_transport=transport)
                    state=rr.execute(work_root=work)['stage_receipts']['enrichment']['accounting']
                    self.assertEqual(state['requests'][failed]['status'],'failed' if failure=='http' else 'uncertain')
                    self.assertFalse(state['complete'])
                    if failure=='interrupt' and failed=='r000001':
                        self.assertEqual(state['requests']['r000002']['status'],'pending')
                        before=pa.tree(work); original=ap.read_bytes(); a=pa.load(ap); a['approved_by']='Changed approver'; ap.write_text(json.dumps(a))
                        with self.assertRaisesRegex(ValueError,'approval-changed'):
                            rr.advance(work,'approved-execute',approval=ap,fixture_transport=transport)
                        self.assertEqual(before,pa.tree(work)); ap.write_bytes(original)
                        source=self.base/'source/main-page.txt'; original=source.read_bytes(); source.write_bytes(b'changed')
                        with self.assertRaises(ValueError): rr.advance(work,'approved-execute',approval=ap,fixture_transport=transport)
                        self.assertEqual(before,pa.tree(work)); source.write_bytes(original)
                    rr.advance(work,'approved-execute',approval=ap,fixture_transport=transport)
                    rr.advance(work,'approved-execute',approval=ap,fixture_transport=transport)
                    self.assertEqual(calls,['r000001','r000002'])
                    exported=review_and_export(work,self.base)
                    self.assertEqual(len(exported['elements']),2)
                    self.assertFalse(exported['execution_complete'])
                    self.assertEqual(exported['request_accounting']['counts']['completed'],1)
                    status=rr.execute(work_root=work)
                    self.assertFalse(status['production_complete']); self.assertEqual(status['completion'],'pending')
                    fake=FakeRclone()
                    published=rr.publish(work,'fake','bucket','gate',runner=fake)
                    self.assertEqual(published['completion'],'offline-full-archive-complete')
                    self.assertFalse(pa.load(work/'completion.json')['requests_successful'])
                    self.assertFalse((work/'enrichment/execution-complete.json').exists())

    def test_route_mismatch_stops_siblings_but_status_remains_readable(self):
        self.plan(selected=False); rr.advance(self.work,'prepare'); ap=count_and_approve(self.work,self.base)
        calls=[]; wrong=inference_double(self.work,wrong_model=True)
        def transport(raw,row): calls.append(row['id']); return wrong(raw,row)
        with self.assertRaisesRegex(ValueError,'model-mismatch'):
            rr.advance(self.work,'approved-execute',approval=ap,fixture_transport=transport)
        state=rr.execute(work_root=self.work)['stage_receipts']['enrichment']['accounting']
        self.assertEqual(state['counts'],dict(pending=1,uncertain=0,failed=1,completed=0))
        with self.assertRaisesRegex(ValueError,'execution-integrity-hold'):
            rr.advance(self.work,'approved-execute',approval=ap,fixture_transport=transport)
        self.assertEqual(calls,['r000001'])

    def test_interruption_consumes_request_without_retry(self):
        self.plan(); rr.advance(self.work,'prepare'); ap=count_and_approve(self.work,self.base)
        rr.advance(self.work,'approved-execute',approval=ap,fixture_transport=inference_double(self.work,interrupt=True))
        state=rr.execute(work_root=self.work)['stage_receipts']['enrichment']['accounting']
        self.assertEqual(state['counts']['uncertain'],1)
        rr.advance(self.work,'approved-execute',approval=ap,fixture_transport=inference_double(self.work))
        self.assertFalse((self.work/'enrichment/execution-complete.json').exists())
    def test_wrong_model_refuses_and_cannot_finalize(self):
        self.plan(); rr.advance(self.work,'prepare'); ap=count_and_approve(self.work,self.base)
        with self.assertRaisesRegex(ValueError,'model-mismatch'): rr.advance(self.work,'approved-execute',approval=ap,fixture_transport=inference_double(self.work,wrong_model=True))
        exported=review_and_export(self.work,self.base)
        self.assertFalse(exported['readiness']['page_ready'])
        self.assertIn('execution-integrity-hold',exported['readiness']['holds'])
    def test_wrong_count_refuses(self):
        self.plan(); rr.advance(self.work,'prepare'); ap=count_and_approve(self.work,self.base)
        with self.assertRaisesRegex(ValueError,'count-mismatch'): rr.advance(self.work,'approved-execute',approval=ap,fixture_transport=inference_double(self.work,wrong_count=True))
    def test_budget_refuses_before_reservation(self):
        self.plan(); rr.advance(self.work,'prepare'); ap=count_and_approve(self.work,self.base)
        a=pa.load(ap); a['maximum_posts']=0; ap.write_text(json.dumps(a))
        with self.assertRaisesRegex(ValueError,'budget'): rr.advance(self.work,'approved-execute',approval=ap,fixture_transport=inference_double(self.work))
        self.assertFalse((self.work/'enrichment'/'execution-start.json').exists())
    def test_fixture_never_live_promoted(self):
        self.plan(); rr.advance(self.work,'prepare'); ap=count_and_approve(self.work,self.base)
        with self.assertRaisesRegex(ValueError,'fixture'): rr.advance(self.work,'approved-execute',approval=ap,authorize=True)
    def test_exact_consumer_refuses_unqualified(self):
        self.ready()
        from qualified_enrichment.exports import exact_view
        view=pa.load(self.work/'export'/'handoff.json')['elements'][0]
        with self.assertRaisesRegex(ValueError,'exact-use'): exact_view(view,'/record',purpose='exact')
        with self.assertRaisesRegex(ValueError,'exact-use'): pa.consume(self.manifest,['main::table-1'],purpose='exact')
    def test_concurrent_page_change_refuses_apply(self):
        self.ready(); rr.candidate_import(self.work,candidate(self.work,self.base))
        self.page.write_text(self.page.read_text()+'Human new edit.\n')
        with self.assertRaisesRegex(ValueError,'page-changed'): rr.apply(self.work,authorize=True)
        self.assertTrue(self.page.read_text().endswith('Human new edit.\n'))
    def test_comments_only_and_annotation_removal_refused(self):
        self.ready(); cp=candidate(self.work,self.base); c=pa.load(cp)
        c['replacements'][0]['new_text']=c['replacements'][0]['new_text'].replace('<!-- Human annotation -->','')
        cp.write_text(json.dumps(c))
        with self.assertRaisesRegex(ValueError,'annotations'): rr.candidate_import(self.work,cp)
    def test_ambiguous_label_and_wrong_identity(self):
        with self.assertRaisesRegex(ValueError,'ambiguous-label'): rr.plan(rr.Request('synthetic',['Table 1']),manifest=self.manifest,work_root=self.work)
        with self.assertRaisesRegex(ValueError,'unknown-article'): rr.plan(rr.Request('other'),manifest=self.manifest,work_root=self.work)
    def test_wrong_page_identity_refused_before_plan(self):
        self.page.write_text(self.page.read_text().replace('slug: synthetic','slug: other-article'))
        with self.assertRaisesRegex(ValueError,'page-article-identity'): self.plan()
        self.assertFalse(self.work.exists())
    def test_page_scope_ignores_frontmatter_and_fenced_headings(self):
        text='---\n# metadata comment\ntitle: Fixture\n---\n# Real\n\n```python\n## Not a section\n```\n<!--\n## Annotation\n-->\n## Results\nText.\n'
        self.assertEqual(set(rr._sections(text)),{'# Real','## Results'})
    def test_unverified_nonfixture_source_cannot_prepare(self):
        self.m['source_status']['fixture']=False
        for d in self.m['documents']: d['fixture']=False
        self.m['provenance']['fixture']=False
        self.manifest.write_text(json.dumps(self.m))
        mapping=pa.load(self.manifest.parent/'local-map.json'); mapping['manifest_sha256']=pa.sha(self.manifest)
        (self.manifest.parent/'local-map.json').write_text(json.dumps(mapping))
        with self.assertRaisesRegex(ValueError,'verified-source-provenance'):
            rr.plan(rr.Request('synthetic',['main::table-1']),manifest=self.manifest,work_root=self.work)
    def test_zero_eligible_full_finishes_without_dummy_requests(self):
        self.m['elements']=[]
        self.manifest.write_text(json.dumps(self.m))
        mapping=pa.load(self.manifest.parent/'local-map.json'); mapping['manifest_sha256']=pa.sha(self.manifest)
        (self.manifest.parent/'local-map.json').write_text(json.dumps(mapping))
        rr.plan(rr.Request('synthetic',None,self.page),manifest=self.manifest,work_root=self.work,fixture=True)
        prepared=rr.advance(self.work,'prepare'); self.assertEqual(prepared['requests'],[])
        ap=count_and_approve(self.work,self.base)
        def never_post(*args): raise AssertionError('zero eligible must not call inference')
        rr.advance(self.work,'approved-execute',approval=ap,fixture_transport=never_post)
        review_and_export(self.work,self.base)
        rr.candidate_import(self.work,candidate(self.work,self.base)); rr.apply(self.work,authorize=True)
        result=rr.publish(self.work,'fake','bucket','zero-gate',runner=FakeRclone())
        self.assertEqual(result['completion'],'offline-full-refresh-complete')
    def test_interrupted_publication_resumes_same_revision(self):
        self.ready(); rr.candidate_import(self.work,candidate(self.work,self.base)); rr.apply(self.work,authorize=True)
        fake=FakeRclone(); fake.fail_after=2
        with self.assertRaises(ValueError): rr.publish(self.work,'fake','bucket','gate',runner=fake)
        before=pa.sha(self.work/'archive'/'manifest.json')
        fake.fail_after=None
        result=rr.publish(self.work,'fake','bucket','gate',runner=fake)
        self.assertEqual(before,pa.sha(self.work/'archive'/'manifest.json'))
        self.assertEqual(result['completion'],'offline-selected-refresh-complete')
    def test_changed_archive_after_interruption_refused(self):
        self.ready(); rr.candidate_import(self.work,candidate(self.work,self.base)); rr.apply(self.work,authorize=True)
        fake=FakeRclone(); fake.fail_after=0
        with self.assertRaises(ValueError): rr.publish(self.work,'fake','bucket','gate',runner=fake)
        archive=self.work/'archive'/'manifest.json'; archive.write_text(archive.read_text()+' ')
        with self.assertRaisesRegex(ValueError,'artifact-changed'): rr.publish(self.work,'fake','bucket','gate',runner=fake)
    def test_changed_count_and_response_refused(self):
        self.ready()
        prepared=pa.load(self.work/'enrichment'/'prepared.json'); row=prepared['requests'][0]
        response=self.work/'enrichment'/row['directory']/'response-body.json'
        response.write_bytes(response.read_bytes()+b' ')
        with self.assertRaisesRegex(ValueError,'binding|artifact-changed'): rr.execute(work_root=self.work)
    def test_selective_cannot_change_unapproved_section(self):
        self.ready(); cp=candidate(self.work,self.base); c=pa.load(cp)
        c['replacements'][0]['heading']='## Unchanged'
        original=(self.work/'original-page.md').read_text(); start,end=rr._sections(original)['## Unchanged']
        c['replacements'][0]['old_sha256']=rr.hashlib_sha(original[start:end]); cp.write_text(json.dumps(c))
        with self.assertRaisesRegex(ValueError,'scope-not-approved'): rr.candidate_import(self.work,cp)
    def test_legacy_wrong_scope_approval_refused(self):
        p=self.plan(legacy=True); ap=self.base/'adopt.json'
        pa.save(ap,dict(plan_sha256=pa.sha(self.work/'plan.json'),manifest_sha256=pa.sha(self.manifest),article=self.m['article'],
            requested_elements=['supplement::table-1'],approved_by='Synthetic',identity_and_scope_reviewed=True))
        with self.assertRaisesRegex(ValueError,'scope-approval'): rr.adopt(self.work,self.manifest,identity_approval=ap)
        self.assertFalse((self.work/'adoption.json').exists())
    def test_cli_persists_plan_and_resume(self):
        env=dict(os.environ)
        cmd=[sys.executable,'-B',str(Path(rr.__file__)),'plan','--article','synthetic','--manifest',str(self.manifest),
             '--element','main::table-1','--fixture','--work-root',str(self.work)]
        result=subprocess.run(cmd,capture_output=True,text=True,timeout=60,env=env)
        self.assertEqual(result.returncode,0,result.stderr)
        result=subprocess.run([sys.executable,'-B',str(Path(rr.__file__)),'execute','--work-root',str(self.work)],capture_output=True,text=True,timeout=60,env=env)
        self.assertEqual(result.returncode,0,result.stderr); self.assertEqual(json.loads(result.stdout)['completion'],'pending')

if __name__=='__main__': unittest.main(verbosity=2)
