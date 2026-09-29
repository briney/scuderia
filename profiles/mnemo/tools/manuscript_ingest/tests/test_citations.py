from test_publication import Publication, MemoryTransport
from manuscript_ingest import workflow as w, sources, archive
from unittest.mock import patch

class Citations(Publication):
    def test_numbered_windows_keep_original_character_offsets(self):
        j,sid=self.ready()
        whole=sources.read(j,[dict(source_id=sid,page=1)],runtime_root=self.runtime)['artifacts']['locations'][0]
        self.assertIn('numbered_text',whole)
        self.assertTrue(whole['numbered_text'].startswith('P1:L1 '))
        chunk=sources.read(j,[dict(source_id=sid,page=1,start_char=10,max_chars=10)],runtime_root=self.runtime)['artifacts']['locations'][0]
        self.assertEqual(chunk['text'],whole['text'][10:20])
        self.assertEqual(chunk['numbered_text'],'P1:L1 '+whole['text'][10:20])
        self.assertEqual(chunk['next_start'],20)

    def test_quotes_archived_clean_page_published_and_revision_bound(self):
        j,sid=self.ready();text=self.draft()+'\nMeasured effect [P1:L1].\nOther [P1:L1, P1:L1-L1].\n'
        r=w.stage(j,text,'Checked the measured result against manuscript page 1.',runtime_root=self.runtime)
        draft=w.job_path(j,self.runtime)/'drafts/1'
        self.assertNotIn('[P1:',(draft/'page.md').read_text())
        evidence=archive.pa.load(draft/'citations.json');self.assertEqual(len(evidence['citations']),3)
        row=evidence['citations'][0];self.assertEqual(row['status'],'located')
        self.assertIn('12 percent',row['segments'][0]['quote'])
        self.assertEqual(row['source_id'],sid)
        self.assertEqual(evidence['draft_sha256'],w.sha(draft/'page.md'))
        manifest=archive.build(j,1,runtime_root=self.runtime);m=archive.verify(manifest)
        self.assertTrue({'citations.json','annotated-page.md'} <= {f['key'] for f in m['files']})
        self.assertEqual(archive.pa.load(manifest.parent/'citations.json')['page_sha256'],w.sha(manifest.parent/'page.md'))
        with patch.object(archive.pa,'RcloneTransport',MemoryTransport),patch.object(w,'integration_check',return_value=[]):
            self.assertEqual(w.publish(j,1,runtime_root=self.runtime)['status'],'complete')
        self.assertNotIn('[P1:',self.page.read_text())
        self.assertFalse(list(self.brain.rglob('citations.json')))

    def test_bad_or_missing_citations_warn_without_hold_or_inference(self):
        j,sid=self.ready()
        r=w.stage(j,self.draft()+'\nUnsupported [P99:L1], malformed [P1:Lx], reversed [P1:L2-L1].\n','Reviewed central findings; optional anchors need correction.',runtime_root=self.runtime)
        self.assertEqual(r['status'],'ready')
        self.assertTrue(r['warnings'])
        draft=w.job_path(j,self.runtime)/'drafts/1';self.assertNotIn('[P',(draft/'page.md').read_text())
        self.assertEqual(len(archive.pa.load(draft/'citations.json')['citations']),3)
        r=w.stage(j,self.draft(),'Checked manuscript findings without optional citation markers.',runtime_root=self.runtime)
        self.assertEqual(r['status'],'ready')
        self.assertFalse(any(v.startswith('Citation locator unresolved:') for v in r['warnings']))
        self.assertFalse((self.runtime/'requests.sqlite').exists())

    def test_citation_product_tamper_blocks_archive_without_rerun(self):
        j,sid=self.ready();w.stage(j,self.draft()+'\nEffect [P1:L1].','Checked measured result against page 1.',runtime_root=self.runtime)
        p=w.job_path(j,self.runtime)/'drafts/1/annotated-page.md'
        p.write_text('Changed annotated draft')
        with self.assertRaisesRegex(ValueError,'citation.*changed'):
            archive.build(j,1,runtime_root=self.runtime)

    def test_multiline_crosspage_body_and_malformed_ranges(self):
        from manuscript_ingest import citations
        j,sid=self.ready();work=w.job_path(j,self.runtime);job=w.load_job(j,self.runtime)
        source=job['sources'][0];first=source['text'][0]
        (work/first['key']).write_text('First line.\nSecond line.\n');first.update(sha256=w.sha(work/first['key']))
        key='text/second.txt';(work/key).write_text('Third line.\nFourth line.\n')
        source.update(pages=2,selected_pages=[1,2]);source['text'].append(dict(page=2,key=key,sha256=w.sha(work/key)))
        clean,ev=citations.extract('Fact [P1:L2-P2:L1]. Other [P2:L1].',job,work)
        self.assertEqual([s['quote'] for s in ev['citations'][0]['segments']],['Second line.','Third line.'])
        self.assertEqual(clean,'Fact. Other.')
        self.assertEqual(citations.numbered('First line.\nSecond line.',1,12,18),'P1:L2 Second')
        import copy
        body=copy.deepcopy(source);body.update(role='body',source_id='s-'+'a'*24);job['sources'].append(body)
        clean,ev=citations.extract('Fact ['+body['source_id']+'/P2:L1].',job,work)
        self.assertEqual(ev['citations'][0]['source_id'],body['source_id'])
        self.assertEqual(ev['citations'][0]['segments'][0]['quote'],'Third line.')
        clean,ev=citations.extract('Fact [P'+('9'*5000)+':L1].',job,work)
        self.assertEqual(ev['citations'][0]['status'],'unresolved')

    def test_preserves_graph_links_markdown_and_canonical_abstract(self):
        from manuscript_ingest import citations
        j,sid=self.ready();job=w.load_job(j,self.runtime);work=w.job_path(j,self.runtime)
        original='See [[P123-domain]] and [P1 residue](https://example.org), [P1:L1][ref], and `[P1:L1]`.\n## Abstract\nLiteral [P1] and [P1:L1] remain verbatim.\n## Findings\nEffect [P1:L1]. Bad [P1:Lx].\n'
        clean,ev=citations.extract(original,job,work)
        self.assertIn('[[P123-domain]]',clean)
        self.assertIn('[P1 residue](https://example.org)',clean)
        self.assertIn('[P1:L1][ref]',clean)
        self.assertIn('`[P1:L1]`',clean)
        self.assertIn('Literal [P1] and [P1:L1] remain verbatim.',clean)
        self.assertIn('Effect. Bad.',clean)
        self.assertEqual([r['status'] for r in ev['citations']],['located','unresolved'])

from test_jobs import only_local_tests
def load_tests(loader,tests,pattern):return only_local_tests(__name__)

class AdjacentLocators(Publication):
    def test_comma_between_locators_does_not_become_prose_punctuation(self):
        from manuscript_ingest import citations
        j,sid=self.ready(); job=w.load_job(j,self.runtime)
        text=self.draft()+'\nModels [P1:L1], [P1:L1], [P1:L1]. Values, however, differ.\n'
        clean,evidence=citations.extract(text,job,w.job_path(j,self.runtime))
        self.assertIn('Models. Values, however, differ.',clean)
        self.assertEqual(len(evidence['citations']),3)

class WrappedLocators(Publication):
    def test_wrapped_groups_and_marker_only_lines_preserve_prose(self):
        from manuscript_ingest import citations
        j,_=self.ready(); job=w.load_job(j,self.runtime)
        clean,ev=citations.extract('Result [P1:L1,\n  P1:L1].\nAnother result\n[P1:L1]. Next sentence.\n\nParagraph [P1:L1].\n',job,w.job_path(j,self.runtime))
        self.assertEqual(clean,'Result.\nAnother result. Next sentence.\n\nParagraph.\n')
        self.assertEqual(len(ev['citations']),4)
        self.assertTrue(all(c['status']=='located' for c in ev['citations']))

class StackedLocators(Publication):
    def test_adjacent_locator_groups_are_all_removed_but_real_reference_links_survive(self):
        from manuscript_ingest import citations
        j,_=self.ready();job=w.load_job(j,self.runtime)
        text='Claim [P1:L1][P1:L1] and [P1:L1] [P1:L1]. Reference [P1:L1][ref].\n'
        clean,evidence=citations.extract(text,job,w.job_path(j,self.runtime))
        self.assertEqual(clean,'Claim and. Reference [P1:L1][ref].\n')
        self.assertEqual(len(evidence['citations']),4)
