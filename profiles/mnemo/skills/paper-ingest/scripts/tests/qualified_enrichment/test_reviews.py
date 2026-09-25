"""Offline review semantics. Synthetic unit data is not model output."""
import copy
import os
from pathlib import Path
import sys
import unittest
ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT), str(ROOT)]
from qualified_enrichment import reviews, exports
from qualified_enrichment.records import digest, project


def element():
    # Explicit synthetic unit fixture: one header contains its unit once.
    return dict(element_id='synthetic-table', source_sha256='a'*64,
        evidence=dict(body_fragments=[dict(fragment_id='f1',page=1,crop='crop.png',crop_sha256='b'*64,
                      native_lines=[dict(line_id='header',text='Distance (angstrom)'),dict(line_id='other',text='Time (s)')])],captions=[]),
        outcome=dict(status='enriched',record=dict(kind='table',cells=[
            dict(row=0,column=0,row_span=1,col_span=1,raw_value='Distance (angstrom)',status='native',
                 source_refs=[dict(fragment_id='f1',line_id='header',start=0,end=len('Distance (angstrom)'))]),
            dict(row=1,column=0,row_span=1,col_span=1,raw_value='3.0',status='native',source_refs=['f1'])],
            rows=[dict(index=0),dict(index=1)],columns=[dict(index=0)],units=[],header_hierarchy={},unresolved=[])))


def reviewer():
    return dict(kind='orchestrator-import',identity='offline-unit-fixture',model=None,provider=None,
                check='Synthetic mechanics; not source validation',timestamp='not-recorded')


def ref(line=0):
    return dict(pointer=f'/body_fragments/0/native_lines/{line}/text',kind='native-text',
                source_sha256='a'*64,text=['Distance (angstrom)','Time (s)'][line])


def setup_review(e=None):
    e = e or element(); dossier=dict(snapshot=dict(elements=[e],source_package='/synthetic/source'))
    packet=reviews.packet_value(dossier,'d'*64,[e['element_id']],1_000_000)
    submission=dict(schema='contextual-review-v1',packet_sha256=digest(packet),reviewer=reviewer(),findings=[],coverage=[],resolutions=[])
    entry=dict(packet=packet,submission=submission,dossier_sha256='d'*64)
    return dossier,entry


def omission(e=None):
    dossier,entry=setup_review(e)
    entry['submission']['findings']=[dict(element_id='synthetic-table',source_sha256='a'*64,
        target='/record/cells/0/raw_value',category='omission',stage='answer',
        reason='Downstream answer omitted the unit already present in native extraction; synthetic analogue, not a VLM error.', evidence=[ref()])]
    return dossier,entry


class Reviews(unittest.TestCase):
    def test_false_empty_findings_do_not_certify_any_scope(self):
        dossier,entry=setup_review()
        v=reviews.apply(dossier,[entry])[0]
        self.assertEqual(v['review_status'],'unreviewed')
        with self.assertRaisesRegex(ValueError,'exact-use-requires'):
            exports.exact_view(v,'/record/cells/0/raw_value',purpose='exact')
        self.assertTrue(exports.exact_view(v,'/record/cells/0/raw_value',purpose='exact',qualification='Unreviewed source copy')['unreviewed_aspects'])

    def test_resolved_copy_has_evidence_and_retains_original(self):
        dossier,entry=omission(); old=copy.deepcopy(dossier)
        first=reviews.apply(dossier,[entry])[0]['findings'][0]
        entry2=copy.deepcopy(entry); entry2['submission']['findings']=[]
        entry2['submission']['resolutions']=[dict(finding_id=first['id'],reason='Literal heading unit retained in qualified copy.',
            basis='literal-copy',evidence=[ref()],agreement='unambiguous',proposed_value='Distance (angstrom)',aspect='units')]
        result=reviews.apply(dossier,[entry,entry2])[0]
        self.assertEqual(result['findings'][0]['status'],'resolved-with-attribution')
        self.assertEqual(result['findings'][0]['stage'],'answer')
        self.assertEqual(dossier,old)
        self.assertEqual(result['outcome']['record']['cells'][0]['raw_value'],'Distance (angstrom)')

    def test_wrong_native_line_in_same_crop_cannot_resolve_unit(self):
        dossier,entry=omission()
        fid=reviews.apply(dossier,[entry])[0]['findings'][0]['id']
        second=copy.deepcopy(entry); second['submission']['findings']=[]
        second['submission']['resolutions']=[dict(finding_id=fid,reason='Incorrect source association negative control',
            basis='literal-copy',evidence=[ref(1)],agreement='unambiguous',proposed_value='Time (s)',aspect='units')]
        with self.assertRaisesRegex(ValueError,'source-association'):
            reviews.apply(dossier,[entry,second])

    def test_bad_targets_hashes_and_literal_selections(self):
        for mode in ('hash','target','source-hash','literal','source-pointer','reason'):
            dossier,entry=omission(); f=entry['submission']['findings'][0]
            if mode=='hash': f['source_sha256']='wrong'
            if mode=='target': f['target']='/record/missing'
            if mode=='source-hash': f['evidence'][0]['source_sha256']='wrong'
            if mode=='literal': f['evidence'][0]['text']='invented unit'
            if mode=='source-pointer': f['evidence'][0]['pointer']='/body_fragments/9/native_text'
            if mode=='reason': f['reason']=' '
            with self.subTest(mode=mode), self.assertRaises(ValueError): reviews.apply(dossier,[entry])

    def test_cell_review_is_not_whole_table_certification(self):
        dossier,entry=setup_review()
        entry['submission']['coverage']=[dict(element_id='synthetic-table',target='/record/cells/0/raw_value',aspect='content',evidence=[ref()],reason='Literal copied content only')]
        v=reviews.apply(dossier,[entry])[0]
        self.assertEqual(v['review_status'],'partially-reviewed')
        self.assertFalse(exports.exact_view(v,'/record/cells/0/raw_value',purpose='summary')['unreviewed_aspects'])
        with self.assertRaises(ValueError): exports.exact_view(v,'/record/cells/0/raw_value',purpose='exact',aspects=['content'])
        with self.assertRaises(ValueError): exports.exact_view(v,'/record',purpose='exact')
        with self.assertRaises(ValueError): exports.exact_view(v,'/record/cells/1/raw_value',purpose='exact')
        entry['submission']['coverage'][0]['aspect']='layout'
        with self.assertRaisesRegex(ValueError,'native-text-cannot-prove-layout'): reviews.apply(dossier,[entry])

    def test_clean_heading_unit_need_not_repeat_in_cells(self):
        e=element(); e['outcome']['record']['cells'][0]['raw_value']='Distance (angstrom)'
        self.assertEqual(project(e)['findings'],[])

    def test_reviewed_scoped_positive_and_ambiguous_range_negative(self):
        dossier,entry=setup_review()
        crop=dict(pointer='/body_fragments/0',kind='crop',source_sha256='a'*64)
        entry['submission']['coverage']=[dict(element_id='synthetic-table',target='/record/cells/0/raw_value',
            aspect=aspect,evidence=[ref(),crop],reason='Synthetic attributed scoped check, not scientific validation') for aspect in reviews.ASPECTS]
        view=reviews.apply(dossier,[entry])[0]
        consumer=exports.exact_view(view,'/record/cells/0/raw_value',purpose='exact')
        self.assertEqual(consumer['scope_review_status'],'reviewed-scoped-content')
        self.assertEqual(consumer['unreviewed_aspects'],[])
        with self.assertRaises(ValueError): exports.exact_view(view,'/record/cells/1/raw_value',purpose='exact')
        dossier,entry=omission(); fid=reviews.apply(dossier,[entry])[0]['findings'][0]['id']
        second=copy.deepcopy(entry); second['submission']['findings']=[]
        sliced=ref(); sliced.update(start=0,end=8,text='Distance')
        second['submission']['resolutions']=[dict(finding_id=fid,reason='Ambiguous shortened heading negative control',
            basis='literal-copy',evidence=[sliced],agreement='unambiguous',proposed_value='Distance',aspect='units')]
        with self.assertRaisesRegex(ValueError,'range-association'): reviews.apply(dossier,[entry,second])

    def test_bounded_packet(self):
        d,e=setup_review()
        with self.assertRaisesRegex(ValueError,'packet-too-large'): reviews.packet_value(d,'d'*64,['synthetic-table'],1024)
        with self.assertRaises(ValueError): reviews.packet_value(d,'d'*64,['nonexistent'],2000)


if __name__=='__main__':
    sys.addaudithook(lambda event,args: (_ for _ in ()).throw(RuntimeError('offline-network-blocked')) if event.startswith('socket.') else None)
    unittest.main(verbosity=2)
