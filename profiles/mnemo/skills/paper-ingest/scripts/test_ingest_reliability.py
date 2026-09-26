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
