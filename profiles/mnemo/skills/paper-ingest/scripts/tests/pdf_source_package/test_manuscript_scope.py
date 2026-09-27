"""Manuscript processing scope never changes retained originals."""
import copy
import os
from pathlib import Path
import tempfile
import unittest
import pymupdf
import source_package as sp


class ManuscriptScope(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(dir=os.environ['PDF_TEST_WORK'])
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        files = []
        for ident, count in [('main', 3), ('si', 2), ('combined', 5), ('data', 0)]:
            path = self.root/(ident + ('.pdf' if count else '.csv'))
            if count:
                with pymupdf.open() as doc:
                    for n in range(count):
                        page = doc.new_page(); page.insert_text((40, 40), f'{ident} page {n+1}')
                    doc.save(path)
            else: path.write_text('value\n7\n')
            files.append(dict(id=ident, role='manuscript' if ident=='main' else 'supplement',
                format='pdf' if count else 'other', path=str(path), sha256=sp.sha(path), filename=path.name,
                source_url='https://example.invalid/'+path.name, discovery_url='https://example.invalid/article',
                article_slug='synthetic', identity_verification=dict(status='operator-verified', basis='Publisher source identity verified')))
        self.value = dict(schema='acquired-sources-v2', article=dict(slug='synthetic', title='Synthetic', doi=None, pmid=None, version='published'),
            files=files, attempts=[], obligations=dict(manuscript=dict(status='retrieved', file_ids=['main']),
                body=dict(status='missing', disposition='Unavailable', attempt_ids=[])),
            attachments=dict(status='advertised', inspected_url='https://example.invalid/article', items=[
                dict(id=f'attachment-{r["id"]}', filename=r['filename'], observed_link=r['source_url'], status='retrieved', file_id=r['id']) for r in files[1:]]),
            processing=dict(policy='manuscript-only-v1', manuscript=dict(source_id='main', pages=[1,2,3], basis='Publisher manuscript boundary verified')))
        files[2]['relationship'] = 'alternative'

    def prepare(self, value=None, name='retained'):
        path = self.root/(name+'.json'); sp.save(path, value or self.value)
        return sp.prepare(path, self.root/name, 'https://example.invalid/v1/chat/completions', 90)

    def test_retain_all_process_only_manuscript_and_preserve_legacy(self):
        result = self.prepare()
        retained, scope = sp.validate_retention(result['retention'])
        self.assertEqual([(d['identity'], d['pages']) for d in scope['documents']], [('main',[1,2,3])])
        self.assertEqual([r['sha256'] for r in retained['acquisition']['files']], [r['sha256'] for r in self.value['files']])
        self.assertEqual([r.get('extraction_disposition') for r in retained['acquisition']['files'][1:]],
            ['retained-unprocessed-supplement', 'retained-unprocessed-alternative', 'retained-unprocessed-supplement'])
        old = copy.deepcopy(self.value); old['schema']='acquired-sources-v1'; del old['processing']; del old['files'][2]['relationship']
        legacy = self.prepare(old, 'legacy')
        self.assertEqual(len(sp.load(legacy['scope'])['documents']), 3)

    def test_composite_alias_keeps_one_original_with_explicit_boundary(self):
        value = copy.deepcopy(self.value); value['files'] = [value['files'][2]]
        row=value['files'][0]; row['role']='manuscript'; del row['relationship']
        value['processing']['manuscript']['source_id']='combined'
        value['obligations']['manuscript']['file_ids']=['combined']
        value['attachments']['items']=[value['attachments']['items'][1]]
        result=self.prepare(value)
        self.assertEqual(sp.load(result['scope'])['documents'][0]['pages'], [1,2,3])
        self.assertEqual(sp.load(result['retention'])['acquisition']['files'][0]['page_count'], 5)

    def test_invalid_scope_and_source_integrity_rejected(self):
        for pages in ([], [0], [4], [1,1], [2,1], [True]):
            value=copy.deepcopy(self.value); value['processing']['manuscript']['pages']=pages
            with self.subTest(pages=pages), self.assertRaises(ValueError): self.prepare(value, 'bad-'+str(pages))
        for field, item in [('source_id','missing'), ('source_id','si'), ('basis','')]:
            value=copy.deepcopy(self.value); value['processing']['manuscript'][field]=item
            with self.subTest(field=field,item=item), self.assertRaises(ValueError): self.prepare(value, 'bad-'+field+'-'+item)
        for index, updates in [(0,dict(sha256='0'*64)), (1,dict(format='other'))]:
            value=copy.deepcopy(self.value); value['files'][index].update(updates)
            with self.assertRaises(ValueError): self.prepare(value, 'bad-file-'+str(index))
        value=copy.deepcopy(self.value); value['processing']['policy']='unknown'
        with self.assertRaises(ValueError): self.prepare(value, 'bad-policy')
