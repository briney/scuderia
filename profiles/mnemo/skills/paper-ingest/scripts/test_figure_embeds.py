import copy
import json
import os
from pathlib import Path
import tempfile
import unittest
from test_article_corrections import synthetic
import final_products as fp
import portable_articles as pa
import figure_embeds as fe

class FigureEmbeds(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(dir=os.environ['SOURCE_PACKAGE_TEST_ROOT']);self.addCleanup(self.tmp.cleanup)
        root=Path(self.tmp.name); manifest,m=synthetic(root)
        # The existing synthetic documents have one element each.
        for i,e in enumerate(m['elements']):
            e['kind']='figure';e['label']='Figure '+str(i+1)
        for i,d in enumerate(m['documents']): d['source_role']='manuscript' if i==0 else 'supplement'
        manifest.write_text(json.dumps(m));mapping=pa.load(manifest.parent/'local-map.json');mapping['manifest_sha256']=pa.sha(manifest);(manifest.parent/'local-map.json').write_text(json.dumps(mapping))
        self.final=root/'package with spaces'; self.m=fp.build(manifest,self.final); self.manifest=self.final/'manifest.json'
        self.page=root/'papers'/'synthetic.md';self.page.parent.mkdir()
        self.text='---\nkind: paper\nslug: synthetic\n---\n\n## Findings\n\nUnchanged research.\n\n## Ingest log\n\nEvidence.\n'
    def test_local_main_figures_and_explicit_supplement(self):
        rendered=fe.render(self.text,self.manifest,self.page)
        self.assertEqual(len(fe.blocks(rendered)),1)
        self.assertIn('package%20with%20spaces',rendered)
        fe.verify(rendered,self.manifest,self.page)
        self.assertEqual(fe.render(rendered,self.manifest,self.page),rendered)
        supplement=self.m['elements'][1]['element_id']
        rendered=fe.render(rendered,self.manifest,self.page,supplements={supplement:'Necessary control for the claim.'})
        self.assertEqual(len(fe.blocks(rendered)),2)
        fe.verify(rendered,self.manifest,self.page)
        with self.assertRaisesRegex(ValueError,'supplement-reason'):
            fe.render(self.text,self.manifest,self.page,supplements={supplement:''})
    def test_manual_edits_and_missing_images_are_not_silent(self):
        rendered=fe.render(self.text,self.manifest,self.page)
        block=fe.blocks(rendered)[0]
        edited=rendered.replace(block[1],block[1]+'Manual caption edit.\n')
        with self.assertRaisesRegex(ValueError,'figure-block-edited'):
            fe.render(edited,self.manifest,self.page)
        body=self.m['elements'][0]['evidence']['body_fragments'][0]['crop']
        (self.final/body).unlink()
        with self.assertRaises(ValueError): fe.verify(rendered,self.manifest,self.page)
    def test_ordered_body_fragments_and_caption_text(self):
        m=copy.deepcopy(self.m);e=m['elements'][0]
        # Repeat a real fragment to exercise ordering without generating images.
        e['evidence']['body_fragments']*=2
        e['evidence']['captions']=[dict(native_text='Panel A: <control> and [dose].')]
        value=fe.figure(e,m,self.page,self.final,reason='')
        self.assertEqual(value.count('!['),2)
        self.assertIn('Source caption',value)
        self.assertNotIn('caption.png',value)
        self.assertIn('\\<control\\>',value)

    def test_refresh_supplement_selection_reaches_publication(self):
        from test_reenrich import ReenrichTests, candidate
        from test_article_corrections import FakeRclone
        import reenrich as rr
        fixture=ReenrichTests('runTest');fixture.setUp();self.addCleanup(fixture.doCleanups)
        for i,e in enumerate(fixture.m['elements']):
            e['kind']=e['content_type']=e['source_element']['content_type']='figure'
        for i,d in enumerate(fixture.m['documents']): d['source_role']='manuscript' if i==0 else 'supplement'
        fixture.manifest.write_text(json.dumps(fixture.m))
        mapping=pa.load(fixture.manifest.parent/'local-map.json');mapping['manifest_sha256']=pa.sha(fixture.manifest)
        (fixture.manifest.parent/'local-map.json').write_text(json.dumps(mapping))
        fixture.ready(selected=False)
        path=candidate(fixture.work,fixture.base);value=pa.load(path)
        value['figure_supplements']={fixture.m['elements'][1]['element_id']:'Necessary control.'}
        path.write_text(json.dumps(value))
        rr.candidate_import(fixture.work,path);rr.apply(fixture.work,authorize=True)
        rr.publish(fixture.work,'fake','bucket','gate',runner=FakeRclone())
        self.assertEqual(fe.verify(fixture.page.read_text(),fixture.work/'archive/manifest.json',fixture.page),2)
        self.assertTrue(pa.load(fixture.work/'completion.json')['figure_embeds'])

    def test_unknown_source_role_does_not_silently_omit_figures(self):
        m=pa.load(self.manifest);m['documents'][0].pop('source_role')
        self.manifest.write_text(json.dumps(m));mapping=pa.load(self.final/'local-map.json')
        mapping['manifest_sha256']=pa.sha(self.manifest);(self.final/'local-map.json').write_text(json.dumps(mapping))
        with self.assertRaisesRegex(ValueError,'figure-source-role-unresolved'):
            fe.render(self.text,self.manifest,self.page)
        with self.assertRaisesRegex(ValueError,'figure-source-role-unresolved'):
            fe.verify(self.text,self.manifest,self.page)
