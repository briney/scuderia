"""Schema-aware review guidance does not invent scientific acceptance."""
import copy
import os
from pathlib import Path
import tempfile
import unittest
from qualified_enrichment import reviews
from test_reviews import element, setup_review, ref

class ReviewGuidance(unittest.TestCase):
    def test_values_and_metadata_warning_are_not_empty_cells(self):
        record=element()['outcome']['record']
        record.update(status='partial',complete=False,provenance_notes=['legacy-metadata-text-unverified'])
        values=['0','007','> 3','5 µg','',None,None]
        statuses=['native','raster','native','raster','blank','unreadable','unresolved']
        record['cells']=[dict(row=i,column=0,row_span=1,col_span=1,raw_value=v,status=status) for i,(v,status) in enumerate(zip(values,statuses))]
        record['rows']=[dict(index=i) for i in range(7)]
        summary=reviews.table_summary(record)
        self.assertEqual([summary[k] for k in ('cell_count','populated_count','blank_count','unreadable_count','unresolved_count')],[7,4,1,1,1])
        self.assertEqual(summary['provenance_notes'],['legacy-metadata-text-unverified'])
        e=element();e['outcome']['record']=record
        dossier,entry=setup_review(e);packet=entry['packet']
        template=reviews.submission_template(packet)
        self.assertIsNone(template['reviewer']['identity'])
        self.assertEqual(template['findings'],[])
        with tempfile.TemporaryDirectory(dir=os.environ['SOURCE_PACKAGE_TEST_ROOT']) as tmp:
            output=Path(tmp)/'packet.json'
            guidance=reviews.write_guidance(packet,output)
            html=Path(guidance['readable_tables']).read_text()
            for literal in ('007','&gt; 3','5 µg'): self.assertIn(literal,html)
        self.assertEqual(record['cells'][1]['raw_value'],'007')

    def test_new_empty_table_claim_rejected_without_invalidating_history(self):
        dossier,entry=setup_review()
        entry['submission']['findings']=[dict(element_id='synthetic-table',source_sha256='a'*64,target='/record',
            category='empty-table-extraction',stage='extraction',reason='All cells are empty',evidence=[ref()])]
        with self.assertRaisesRegex(ValueError,'populated=2'):
            reviews.apply(dossier,[entry],validate_new=True)
        # Reconstruction preserves what the old reviewer actually submitted.
        self.assertEqual(len(reviews.apply(dossier,[entry])[0]['findings']),1)

    def test_packet_batches_account_for_oversized_source_inspection(self):
        first=element(); second=copy.deepcopy(first);second['element_id']='second'
        large=copy.deepcopy(first);large['element_id']='large';large['outcome']['record']['cells'][0]['raw_value']='x'*20000
        dossier=dict(schema='uncertainty-dossier-v2',policy='observed-limitations-v1',
            snapshot=dict(elements=[first,second,large],source_package='/synthetic',source_files=[]))
        batches=reviews.packet_batches(dossier,'d'*64,8000)
        self.assertEqual([e['element_id'] for packet in batches['packets'] for e in packet['elements']],['synthetic-table','second'])
        self.assertEqual(batches['oversized'],['large'])
        source=reviews.packet_value(dossier,'d'*64,[],8000)
        self.assertIsNone(reviews.submission_template(source)['assessment']['usable_evidence'])
