"""Portable contract regressions, synthetic evidence only; no network."""
import copy
import hashlib
import json
import os
from pathlib import Path
import shutil
import tempfile
import unittest

import portable_articles as pa
import reenrich as rr


def synthetic(root):
    """Schema-valid synthetic archive, with two document-scoped same-label elements."""
    source = root / 'source'
    source.mkdir()
    files, mapping, documents, elements = [], {}, [], []
    for doc in ('main', 'supplement'):
        raw = source / (doc + '.pdf')
        raw.write_bytes(b'Synthetic source, not a scientific PDF: ' + doc.encode())
        h = pa.sha(raw)
        deps = []
        for name, data in [('original.pdf', raw.read_bytes()), ('page.txt', b'Header (mg), footnote: uncertain'),
                           ('crop.png', b'Synthetic image bytes'), ('caption.txt', b'Table 1: uncertain units')]:
            key = 'package/' + doc + '/' + name
            p = source / (doc + '-' + name)
            p.write_bytes(data)
            files.append(pa.file_record('source-package', key, p))
            mapping[key] = dict(root=str(source), path=p.name)
            deps.append(key)
        documents.append(dict(identity=doc, source_sha256=h, source_version='synthetic-v1',
                              source_id=doc, raw_key=deps[0], complete=True, fixture=True, gaps=[]))
        elements.append(dict(element_id=doc+'::table-1', document=doc, source_sha256=h,
            content_type='table', kind='table', eligible=True, label='Table 1',
            fragments=[dict(fragment_id=doc+'::fragment', page=1, bbox=[0,0,10,10],
                            crop_key=deps[2], crop_sha256=files[-2]['sha256'])],
            caption_note_refs=[], dependencies=deps, unavailable=[],
            evidence=dict(element_id=doc+'::table-1', source_document=doc, source_sha256=h,
                label='Table 1', body_fragments=[dict(fragment_id=doc+'::fragment',page=1,bbox=[0,0,10,10],
                    crop=deps[2],crop_sha256=files[-2]['sha256'],native_lines=[])], captions=[]),
            source_element=dict(id=doc+'::table-1', source_document=doc, content_type='table'),
            context=dict(native_text_keys=[deps[1]], heading_unit_footnote_scope='whole physical page'),
            inherited=[]))
    warning = source / 'findings.json'
    warning.write_text(json.dumps({'notice':'Known unit uncertainty; original unchanged'}))
    key = 'review/findings.json'
    files.append(pa.file_record('enrichment-review', key, warning))
    mapping[key] = dict(root=str(source),path=warning.name)
    for e in elements:
        e['dependencies'].append(key)
        e['inherited'].append(key)
    value = dict(schema=pa.SCHEMA, package_id='synthetic-revision', article=dict(slug='synthetic',title='Synthetic',doi=None,pmid=None,version='v1'),
        article_key=pa.article_key(dict(slug='synthetic',doi=None,pmid=None)),
        files=files,total_objects=len(files),documents=documents,elements=elements,
        common_dependencies=[key], dispositions=[],source_status=dict(complete=True,fixture=True,holds=[],
            identity_basis='Synthetic operator assertion, never production', acquisition_verified=True,
            extraction_verified=True),provenance={'fixture':True})
    out=root/'archive'; out.mkdir()
    pa.save(out/'manifest.json',value)
    pa.save(out/'local-map.json',dict(schema='portable-article-local-map-v2',manifest_sha256=pa.sha(out/'manifest.json'),sources=mapping))
    return out/'manifest.json',value


class FakeRclone:
    def __init__(self):
        self.store={}; self.calls=[]; self.corrupt=None; self.fail_after=None
    def __call__(self, argv, *, output=None, timeout=300):
        self.calls.append(argv)
        target=next(a for a in argv if a.startswith('fake:'))
        key=target.split('/',1)[1]
        if argv[1]=='lsf': return key.rsplit('/',1)[-1]+'\n' if key in self.store else ''
        if argv[1]=='copyto':
            if self.fail_after is not None and len(self.store)>=self.fail_after: raise ValueError('injected-transfer-interruption')
            if key not in self.store: self.store[key]=Path(argv[2]).read_bytes()
            if self.corrupt==key: self.store[key]=b'corrupt'
            return ''
        if argv[1]=='cat':
            if key not in self.store: raise ValueError('missing-remote-object')
            data=self.store[key]
            if '--count' in argv: data=data[:int(argv[argv.index('--count')+1])]
            output.write(data)
            return ''
        raise AssertionError(argv)


class Corrections(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(dir=os.environ['SOURCE_PACKAGE_TEST_ROOT'],prefix='contract-')
        self.addCleanup(self.tmp.cleanup); self.root=Path(self.tmp.name)
        self.path,self.value=synthetic(self.root)
    def test_shared_article_objects_across_revisions(self):
        fake=FakeRclone(); first=pa.publish(self.path,'fake','bucket','gate',runner=fake)
        newer=copy.deepcopy(self.value); newer['package_id']='revision-two'
        new=self.root/'new-output.txt'; new.write_text('new enrichment output')
        record=pa.file_record('handoff','new/output.txt',new)
        newer['files'].append(record); newer['total_objects']+=1
        root=self.root/'revision-two'; root.mkdir(); pa.save(root/'manifest.json',newer)
        mapping=pa.local_sources(self.path); mapping[record['key']]=dict(root=str(self.root),path=new.name)
        pa.save(root/'local-map.json',dict(schema='portable-article-local-map-v2',manifest_sha256=pa.sha(root/'manifest.json'),sources=mapping))
        second=pa.publish(root/'manifest.json','fake','bucket','gate',runner=fake)
        self.assertEqual(second['uploaded'],2)
        for f in self.value['files']:
            key=pa.object_key(self.value,'gate',f)
            self.assertEqual(key,pa.object_key(newer,'gate',f))
            self.assertTrue(any(r['key']==key and r['reused'] and r['method']=='read_back_sha256' for r in second['receipts']))
        self.assertNotEqual(first['manifest_key'],second['manifest_key'])
        fake.corrupt=None
        fake.store[pa.object_key(newer,'gate',newer['files'][0])]=b'bad'
        with self.assertRaises(ValueError): pa.publish(root/'manifest.json','fake','bucket','gate',runner=fake)

    def test_v2_layout_read_support_does_not_repin(self):
        legacy=copy.deepcopy(self.value); legacy['schema']='portable-article-manifest-v2'
        self.path.write_text(json.dumps(legacy)); mapping=pa.load(self.path.parent/'local-map.json')
        mapping['manifest_sha256']=pa.sha(self.path); (self.path.parent/'local-map.json').write_text(json.dumps(mapping))
        before=pa.sha(self.path); fake=FakeRclone(); pub=pa.publish(self.path,'fake','bucket','gate',runner=fake)
        self.assertIn('/revisions/synthetic-revision/objects/',pa.object_key(legacy,'gate',legacy['files'][0]))
        pa.restore_remote(pub['manifest_key'],before,self.root/'legacy',remote='fake',bucket='bucket',prefix='gate',article_key=legacy['article_key'],runner=fake)
        self.assertEqual(pa.sha(self.root/'legacy'/'manifest.json'),before)

    def test_history_projects_warnings_without_raw_wire_bodies(self):
        wire=self.root/'source'/'request-wire.json'
        wire.write_text(json.dumps({'messages':[{'content':'data:image/png;base64,NEVER_COPY_RAW_WIRE'}]}))
        key='job/request-wire.json'; self.value['files'].append(pa.file_record('enrichment-job',key,wire))
        self.value['total_objects']+=1; self.value['common_dependencies'].append(key)
        self.path.write_text(json.dumps(self.value)); mapping=pa.load(self.path.parent/'local-map.json')
        mapping['sources'][key]=dict(root=str(wire.parent),path=wire.name); mapping['manifest_sha256']=pa.sha(self.path)
        (self.path.parent/'local-map.json').write_text(json.dumps(mapping))
        result=pa.consume(self.path,['main::table-1'])
        self.assertIn('Known unit uncertainty',json.dumps(result))
        self.assertNotIn('NEVER_COPY_RAW_WIRE',json.dumps(result))
        self.assertTrue(any(r['key']==key and r['sha256']==pa.sha(wire) for r in result['history']))
        self.assertTrue(all('content' not in r and 'local_path' not in r for r in result['history']))

    def test_prompt_history_is_scoped_deduplicated_not_archive_inventory(self):
        import article_enrichment as ae
        from article_runtime import trusted_modules
        trusted_modules()
        e=self.value['elements'][0]; other=self.value['elements'][1]
        sources=pa.local_sources(self.path)
        records={
            'review/scoped.json': dict(reviewer={'identity':'Reviewer A'}, findings=[
                dict(element_id=e['element_id'],source_sha256=e['source_sha256'],reason='RELEVANT unresolved units'),
                dict(element_id=e['element_id'],source_sha256=other['source_sha256'],reason='WRONG SOURCE same ID'),
                dict(document='supplement',label='Table 1',reason='OTHER DOCUMENT same label'),
                dict(reason='UNKNOWN SCOPE warning')]),
            'review/empty.json': dict(warnings=[],uncertainty=None),
            'review/export.json': dict(schema='portable-qualified-export-v3',elements=[],warnings=['UNSCOPED export warning']),
            'package/manifest.json': dict(schema='pdf-source-package-v1',documents=[
                dict(identity='main',directory='documents/main',sha256=e['source_sha256']),
                dict(identity='supplement',directory='documents/supplement',sha256=other['source_sha256'])]),
            'package/initial-plan.json': dict(phase='initial',requests=[
                dict(document='supplement',directory='requests/other')]),
            'package/requests/other/decoded.json': dict(warnings=['OTHER REQUEST warning']),
            'package/documents/supplement/inventory.json': dict(limitations=['OTHER INVENTORY limitation']),
            'package/documents/main/inventory.json': dict(limitations=['RELEVANT source limitation']),
            'review/duplicate.json': dict(warnings=['DUPLICATE unresolved warning']),
            'review/decoded.json': dict(mapped=dict(warnings=['DUPLICATE unresolved warning'])),
        }
        for i,(key,value) in enumerate(records.items()):
            p=self.root/'source'/('history-'+str(i)+'.json'); pa.save(p,value)
            sources[key]=dict(root=str(p.parent),path=p.name)
            self.value['files'].append(pa.file_record('enrichment-review',key,p))
            self.value['common_dependencies'].append(key)
            e['inherited'].append(key); e['dependencies'].append(key)
        self.value['total_objects']=len(self.value['files'])
        self.path.write_text(json.dumps(self.value))
        (self.path.parent/'local-map.json').write_text(json.dumps(dict(schema='portable-article-local-map-v2',manifest_sha256=pa.sha(self.path),sources=sources)))
        _,paths=pa.verify_local(self.path)
        before=pa.tree(self.root/'source')
        wire,_,_=ae.wire_for(e,paths,ae.DEFAULT_PROFILE)
        text=json.dumps(wire)
        for warning in ('Known unit uncertainty','RELEVANT unresolved units','RELEVANT source limitation','UNKNOWN SCOPE warning','Reviewer A','UNSCOPED export warning'):
            self.assertIn(warning,text)
        for warning in ('WRONG SOURCE','OTHER DOCUMENT','OTHER REQUEST','OTHER INVENTORY','review/empty.json'):
            self.assertNotIn(warning,text)
        self.assertEqual(text.count('DUPLICATE unresolved warning'),1)
        self.assertIn('unscoped',text)
        consumer=pa.consume(self.path,[e['element_id']])
        self.assertIn('OTHER DOCUMENT',json.dumps(consumer))
        self.assertEqual(before,pa.tree(self.root/'source'))
        self.assertEqual({r['key'] for r in consumer['history']},set(e['inherited']))

    def test_positive_local_restore_and_consume(self):
        out=self.root/'restored'; result=pa.restore(self.path,out,elements=['main::table-1'])
        self.assertEqual(result['completed'],'selected-elements')
        shutil.rmtree(self.root/'source')
        consumer=pa.consume(out/'manifest.json',['main::table-1'])
        self.assertIn('Known unit uncertainty',json.dumps(consumer))
        self.assertFalse(any('/supplement/' in k for k in result['restored']))
        self.assertIn('review/findings.json',result['restored'])
        self.assertEqual(pa.load(out/'manifest.json'),self.value)
    def test_remote_manifest_roundtrip(self):
        fake=FakeRclone(); prefix='gate'
        pub=pa.publish(self.path,'fake','bucket',prefix,runner=fake)
        self.assertNotIn('sources',json.loads(fake.store[pub['manifest_key']]))
        shutil.rmtree(self.root/'source'); shutil.rmtree(self.path.parent)
        result=pa.restore_remote(pub['manifest_key'],pub['manifest_sha256'],self.root/'remote',
            remote='fake',bucket='bucket',prefix=prefix,article_key=self.value['article_key'],runner=fake)
        self.assertEqual(result['completed'],'full-package')
        pa.consume(self.root/'remote'/'manifest.json',['main::table-1'])
    def test_no_false_full_with_exclusions(self):
        result=pa.restore(self.path,self.root/'partial',include_enrichment=False)
        self.assertEqual(result['completed'],'partial-package')
        with self.assertRaises(ValueError): pa.consume(self.root/'partial'/'manifest.json',['main::table-1'])
    def test_unsafe_alias_and_missing_dependency_rejected_before_write(self):
        for change in ('alias','missing','size'):
            v=copy.deepcopy(self.value)
            if change=='alias': v['files'][0]['key']='package//main/original.pdf'
            if change=='missing': v['elements'][0]['dependencies'].append('package/missing.txt')
            if change=='size': v['files'][0]['size']=-1
            bad=self.root/(change+'.json'); pa.save(bad,v)
            with self.assertRaises(ValueError): pa.restore(bad,self.root/(change+'-out'))
            self.assertFalse((self.root/(change+'-out')).exists())
    def test_tamper_after_plan_and_no_false_complete(self):
        work=self.root/'work'
        p=rr.plan(rr.Request('synthetic',['main::table-1']),manifest=self.path,work_root=work,fixture=True)
        result=rr.execute(p,work_root=work)
        self.assertNotIn('complete',result['completion'])
        (self.root/'source'/'main-page.txt').write_text('tampered')
        with self.assertRaises(ValueError): rr.execute(p,work_root=work)
    def test_manifest_plan_binding(self):
        work=self.root/'work'
        p=rr.plan(rr.Request('synthetic',['main::table-1']),manifest=self.path,work_root=work,fixture=True)
        self.path.write_text(self.path.read_text()+' ')
        with self.assertRaises(ValueError): rr.execute(p,work_root=work)
    def test_zero_elements_archive_allowed(self):
        v=copy.deepcopy(self.value); v['elements']=[]
        pa.validate_manifest(v)
    def test_corrupt_remote_never_publishes_manifest(self):
        fake=FakeRclone()
        first=self.value['files'][0]
        fake.corrupt=pa.object_key(self.value,'gate',first)
        with self.assertRaises(ValueError): pa.publish(self.path,'fake','bucket','gate',runner=fake)
        self.assertFalse(any('/manifests/' in k for k in fake.store))
    def test_omitted_review_dependency_rejected(self):
        v=copy.deepcopy(self.value); v['common_dependencies']=[]
        for e in v['elements']:
            e['inherited']=[]; e['dependencies'].remove('review/findings.json')
        with self.assertRaisesRegex(ValueError,'omitted-review'): pa.validate_manifest(v)
    def test_document_version_and_crop_hash_mismatch(self):
        for field in ('source_sha256','crop_sha256'):
            v=copy.deepcopy(self.value)
            if field=='source_sha256': v['elements'][0][field]='0'*64
            else: v['elements'][0]['fragments'][0][field]='0'*64
            with self.assertRaises(ValueError): pa.validate_manifest(v)
    def test_remote_size_and_hash_corruption(self):
        for corruption in ('size','hash'):
            fake=FakeRclone(); pub=pa.publish(self.path,'fake','bucket','gate',runner=fake)
            f=self.value['files'][0]; key=pa.object_key(self.value,'gate',f)
            raw=fake.store[key]; fake.store[key]=raw+b'x' if corruption=='size' else b'x'*len(raw)
            with self.assertRaises(ValueError): pa.restore_remote(pub['manifest_key'],pub['manifest_sha256'],self.root/corruption,
                remote='fake',bucket='bucket',prefix='gate',article_key=self.value['article_key'],runner=fake)
            self.assertFalse((self.root/corruption/'RESTORE-RECEIPT.json').exists())
    def test_unsafe_all_keys_before_any_write(self):
        for number,key in enumerate(('package/../escape','package//alias','package/./alias','package/alias/','package/\\\\escape','/absolute')):
            v=copy.deepcopy(self.value); v['files'][-1]['key']=key
            bad=self.root/('unsafe-'+str(number)+'.json'); pa.save(bad,v)
            output=self.root/('out-'+str(number))
            with self.assertRaises(ValueError): pa.restore(bad,output)
            self.assertFalse(output.exists())
    def test_symlink_source_and_output_refused(self):
        source=self.root/'source'/'main-page.txt'; raw=source.read_bytes(); source.unlink()
        actual=self.root/'actual.txt'; actual.write_bytes(raw); source.symlink_to(actual)
        with self.assertRaises(ValueError): pa.restore(self.path,self.root/'bad')
        output=self.root/'symlink'; output.symlink_to(self.root/'absent')
        with self.assertRaises(ValueError): pa.restore(self.path,output)
    def test_real_rclone_local_cli_remote_manifest_roundtrip(self):
        # The real subprocess adapter, using rclone's local backend, never R2.
        import subprocess, sys
        env=dict(os.environ,RCLONE_CONFIG=str(self.root/'empty-rclone.conf'),RCLONE_CONFIG_OFFLINE_TYPE='local')
        (self.root/'empty-rclone.conf').write_text('')
        command=[sys.executable,'-B',str(Path(pa.__file__))]
        pub=subprocess.run(command+['publish','--manifest',str(self.path),'--remote','offline','--bucket','bucket','--prefix','gate'],
            cwd=self.root,capture_output=True,text=True,timeout=120,env=env)
        self.assertEqual(pub.returncode,0,pub.stderr)
        receipt=json.loads(pub.stdout)
        shutil.rmtree(self.root/'source'); shutil.rmtree(self.path.parent)
        result=subprocess.run(command+['restore','--manifest-key',receipt['manifest_key'],'--manifest-sha256',receipt['manifest_sha256'],
            '--remote','offline','--bucket','bucket','--prefix','gate','--article-key',self.value['article_key'],'--destination',str(self.root/'restored')],
            cwd=self.root,capture_output=True,text=True,timeout=120,env=env)
        self.assertEqual(result.returncode,0,result.stderr)
        self.assertEqual(json.loads(result.stdout)['completed'],'full-package')
        pa.verify_local(self.root/'restored'/'manifest.json')
    def test_subprocess_timeout_becomes_hold(self):
        import subprocess
        from unittest.mock import patch
        with patch('portable_articles.subprocess.run',side_effect=subprocess.TimeoutExpired('rclone',300)):
            with self.assertRaisesRegex(ValueError,'rclone-timeout'): pa._run_rclone(['rclone','lsf','fake:bucket/object'])
    def test_hardlink_refused(self):
        target=self.root/'source'/'main-page.txt'
        os.link(target,self.root/'alias')
        with self.assertRaises(ValueError): pa.restore(self.path,self.root/'out')

if __name__=='__main__': unittest.main(verbosity=2)
