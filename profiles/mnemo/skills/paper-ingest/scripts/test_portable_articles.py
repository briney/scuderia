"""Archive tests built from real retained acquisition and accepted extraction.

The supplied donor is READ ONLY. Every changed file belongs to this test's
new scratch directory; historical embedded paths are never followed for writes.
"""
import copy
import json
import os
from pathlib import Path
import shutil
import tempfile
import unittest

import portable_articles as pa
import source_package as sp
from test_article_corrections import FakeRclone


def real_archive(base):
    donor=Path(os.environ['PORTABLE_ARTICLES_DONOR'])
    donor_manifest=pa.load(donor/'manifest.json')
    inputs=base/'inputs'; inputs.mkdir()
    article=dict(slug='portable-fixture',title='Synthetic identity for offline byte-preservation tests',doi=None,pmid=None,version='fixture-v1')
    files=[]; bindings={}
    for i,doc in enumerate(donor_manifest['documents']):
        source=inputs/('source-'+str(i)+'.pdf'); shutil.copyfile(donor/doc['raw'],source)
        ident='source-'+str(i); role='manuscript' if i==0 else 'supplement'
        files.append(dict(id=ident,path=str(source),sha256=pa.sha(source),filename=source.name,role=role,format='pdf',
            source_url='https://example.invalid/source',discovery_url='https://example.invalid/article',article_slug=article['slug'],
            identity_verification=dict(status='operator-verified',basis='Explicit synthetic fixture label on copied donor bytes; never a scientific assertion.')))
        bindings[doc['identity']]=ident
    body=inputs/'body.txt'; body.write_text('Synthetic body, not scientific evidence.')
    files.append(dict(id='body',path=str(body),sha256=pa.sha(body),filename='body.txt',role='body',format='other',
        source_url='https://example.invalid/body',discovery_url='https://example.invalid/article',article_slug=article['slug'],
        identity_verification=dict(status='operator-verified',basis='Synthetic fixture body.')))
    attachments=[dict(id=f['id'],observed_link=f['source_url'],filename=f['filename'],status='retrieved',file_id=f['id'])
                 for f in files if f['role']=='supplement']
    value=dict(schema='acquired-sources-v1',article=article,files=files,attempts=[],
        obligations=dict(body=dict(status='retrieved',file_ids=['body']),manuscript=dict(status='retrieved',file_ids=['source-0'])),
        attachments=dict(status='advertised' if attachments else 'none-listed',inspected_url='https://example.invalid/article',items=attachments))
    pa.save(base/'acquired.json',value)
    sp.prepare(base/'acquired.json',base/'retention','https://example.invalid/v1/chat/completions',120)
    shutil.copytree(donor,base/'package',ignore=shutil.ignore_patterns('__pycache__','*.pyc'))
    m=pa.build_manifest(base/'retention'/'retention.json',base/'package',base/'archive',package_id='fixture-01',document_bindings=bindings)
    return base/'archive'/'manifest.json',m,bindings


class RealArchiveTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp=tempfile.TemporaryDirectory(dir=os.environ['SOURCE_PACKAGE_TEST_ROOT'],prefix='real-archive-')
        cls.base=Path(cls.tmp.name)
        cls.path,cls.m,cls.bindings=real_archive(cls.base)
    @classmethod
    def tearDownClass(cls): cls.tmp.cleanup()
    def directory(self):
        t=tempfile.TemporaryDirectory(dir=self.base,prefix='test-'); self.addCleanup(t.cleanup); return Path(t.name)
    def test_real_manifest_retains_source_bindings_and_identity(self):
        m,paths=pa.verify_local(self.path)
        self.assertIn('retention/retention.json',paths)
        self.assertTrue(m['elements'])
        self.assertNotIn('sources',m)
        for d in m['documents']:
            original=next(r for r in m['files'] if r.get('binds',{}).get('source_id')==d['source_id'])
            self.assertEqual(original['sha256'],d['source_sha256'])
        self.assertIn('attempts',[r['kind'] for r in m['dispositions']])
    def test_full_restore_all_bytes(self):
        root=self.directory(); result=pa.restore(self.path,root/'restored')
        self.assertEqual(result['completed'],'full-package'); self.assertEqual(result['restored_count'],self.m['total_objects'])
        pa.verify_local(root/'restored'/'manifest.json')
    def test_selected_restore_native_caption_context(self):
        root=self.directory(); e=self.m['elements'][0]
        result=pa.restore(self.path,root/'selected',elements=[e['element_id']])
        self.assertLess(result['restored_count'],self.m['total_objects'])
        for cap in e['evidence']['captions']: self.assertIn(cap['crop'],result['restored'])
        for key in e['context']['native_text_keys']: self.assertIn(key,result['restored'])
        pa.consume(root/'selected'/'manifest.json',[e['element_id']])
    def test_publish_reuse_readback_and_manifest_last(self):
        fake=FakeRclone(); result=pa.publish(self.path,'fake','bucket','gate',runner=fake)
        self.assertEqual(result['objects'],self.m['total_objects'])
        uploads=[c for c in fake.calls if c[1]=='copyto']; self.assertIn('/manifests/',uploads[-1][3])
        self.assertTrue(all('--immutable' in c and '--ignore-existing' in c for c in uploads))
        result=pa.publish(self.path,'fake','bucket','gate',runner=fake); self.assertEqual(result['uploaded'],0)
    def test_corrupt_remote_manifest(self):
        fake=FakeRclone(); pub=pa.publish(self.path,'fake','bucket','gate',runner=fake)
        fake.store[pub['manifest_key']]+=b'x'; root=self.directory()
        with self.assertRaises(ValueError): pa.restore_remote(pub['manifest_key'],pub['manifest_sha256'],root/'bad',
            remote='fake',bucket='bucket',prefix='gate',article_key=self.m['article_key'],runner=fake)
        self.assertFalse((root/'bad').exists())
    def test_wrong_trusted_prefix_rejected(self):
        fake=FakeRclone(); root=self.directory()
        with self.assertRaises(ValueError): pa.restore_remote('untrusted/manifests/'+'0'*64+'.json','0'*64,root/'bad',
            remote='fake',bucket='bucket',prefix='gate',article_key=self.m['article_key'],runner=fake)
        self.assertEqual(fake.calls,[])
    def test_interrupted_publish_never_announces(self):
        fake=FakeRclone(); fake.fail_after=2
        with self.assertRaisesRegex(ValueError,'interruption'): pa.publish(self.path,'fake','bucket','gate',runner=fake)
        self.assertFalse(any('/manifests/' in k for k in fake.store))
    def test_empty_unknown_selection_refused(self):
        root=self.directory()
        for elements in ([],['missing-element']):
            with self.assertRaises(ValueError): pa.restore(self.path,root/'bad',elements=elements)
    def test_source_association_cannot_be_overridden(self):
        root=self.directory()
        wrong={k:'not-the-acquired-source' for k in self.bindings}
        with self.assertRaisesRegex(ValueError,'association'): pa.build_manifest(self.base/'retention'/'retention.json',self.base/'package',root/'bad',
            package_id='wrong',document_bindings=wrong)
        with self.assertRaisesRegex(ValueError,'identity'): pa.build_manifest(self.base/'retention'/'retention.json',self.base/'package',root/'bad',
            package_id='wrong',article=dict(slug='other'),document_bindings=self.bindings)
    def test_local_map_escape_refused(self):
        root=self.directory(); shutil.copyfile(self.path,root/'manifest.json')
        mapping=pa.load(self.path.parent/'local-map.json'); first=next(iter(mapping['sources']))
        mapping['sources'][first]['path']='/absolute/escape'
        pa.save(root/'local-map.json',mapping)
        with self.assertRaises(ValueError): pa.restore(root/'manifest.json',root/'bad')
        self.assertFalse((root/'bad').exists())

if __name__=='__main__': unittest.main(verbosity=2)
