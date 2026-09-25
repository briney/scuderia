"""Synthetic resolution controls; no scientific observations or model output."""
import copy
import html
import json
import os
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT), str(ROOT)]
from qualified_enrichment import exports, reviews
from qualified_enrichment.records import digest, project
from test_reviews import element, setup_review, ref


def crop():
    return dict(pointer='/body_fragments/0', kind='crop', source_sha256='a'*64)


def finding_entry(e, target, stage='extraction'):
    dossier, entry = setup_review(e)
    entry['submission']['findings'] = [dict(element_id=e['element_id'], source_sha256=e['source_sha256'],
        target=target, category='synthetic-issue', stage=stage, reason='Synthetic omitted unit.', evidence=[crop()])]
    issue = next(f for f in reviews.apply(dossier, [entry])[0]['findings'] if f['category'] == 'synthetic-issue')
    return dossier, entry, issue


def resolution(entry, issue, proposed, *, basis='source-inspection', aspect='units', identity='reviewer-one'):
    result = copy.deepcopy(entry)
    result['submission'].update(findings=[], coverage=[], resolutions=[dict(finding_id=issue['id'],
        reason='Synthetic attributed source reading.', basis=basis, evidence=[ref()] if basis == 'literal-copy' else [crop()],
        agreement='unambiguous', proposed_value=proposed, aspect=aspect)])
    result['submission']['reviewer']['identity'] = identity
    return result


def cover(entry, e, target):
    entry['submission']['coverage'] = [dict(element_id=e['element_id'], target=target, aspect=a,
        evidence=[crop(), ref()], reason='Synthetic scoped coverage, not scientific verification.') for a in reviews.ASPECTS]


def register(view):
    sys.path.insert(0, os.environ['UNCERTAINTY_ADAPTER'])
    import source_package
    return source_package.qualification_text(dict(schema='qualified-enrichment-export-v1',elements=[view], eligibility=dict(element_accounting=[], zero_eligible=False)))


class ResolutionAnnotations(unittest.TestCase):
    def test_changed_original_is_qualified_in_all_shared_consumers(self):
        for kind in ('table', 'figure', 'embedded-table', 'algorithm'):
            with self.subTest(kind=kind):
                e = element()
                e['outcome']['record']['cells'][0]['raw_value'] = 'Distance'
                target = '/record/cells/0/raw_value'
                if kind == 'embedded-table':
                    e['outcome']['record'] = dict(kind='figure', embedded_tables=[e['outcome']['record']])
                    target = '/record/embedded_tables/0/cells/0/raw_value'
                elif kind in ('figure', 'algorithm'):
                    group = 'observations' if kind == 'figure' else 'lines'
                    e['outcome']['record'] = dict(kind=kind, **{group: [dict(text='Distance', source_refs=['f1'])]})
                    target = '/record/'+group+'/0/text'
                before = digest(e)
                d, first, issue = finding_entry(e, target)
                second = resolution(first, issue, 'Distance (angstrom)')
                cover(second, e, target)
                view = reviews.apply(d, [first, second])[0]
                for purpose in ('discovery', 'summary', 'exact'):
                    result = exports.exact_view(view, target, purpose=purpose,
                        **({'qualification': 'Original is unchanged; retain the attributed correction.'} if purpose == 'exact' else {}))
                    self.assertEqual(result['content'], 'Distance')
                    self.assertIn(issue['id'], json.dumps(result))
                    self.assertIn('Distance (angstrom)', json.dumps(result))
                    self.assertIn('reviewer-one', json.dumps(result))
                with self.assertRaisesRegex(ValueError, 'exact-use-requires'):
                    exports.exact_view(view, target, purpose='exact')
                readable = html.unescape(exports.render_record(view, view['outcome']['record']))
                self.assertIn(issue['id'], readable)
                self.assertIn('Distance (angstrom)', readable)
                self.assertIn('reviewer-one', readable)
                self.assertEqual(digest(e), before)

    def test_parent_summary_resolution_remains_visible_at_child_content(self):
        e = element(); record = e['outcome']['record']
        record.update(status='partial', source_refs=['f1'])
        record['cells'][1]['status'] = 'partial'
        d, first = setup_review(e)
        issue = next(f for f in project(e)['findings'] if f['target'] == '/record')
        self.assertTrue(issue['summary_only'])
        proposed = copy.deepcopy(record); proposed['cells'][0]['raw_value'] = 'Distance (nm)'
        decisions = [resolution(first, issue, proposed, aspect=a) for a in reviews.ASPECTS]
        view = reviews.apply(d, decisions)[0]
        consumer = exports.exact_view(view, '/record/cells/0/raw_value')
        self.assertIn(issue['id'], json.dumps(consumer))
        self.assertIn('Distance (nm)', json.dumps(consumer))
        self.assertIn('Distance (nm)', html.unescape(exports.warning_html(view, '/record/cells/0')))

    def test_adapter_register_retains_resolved_correction_and_provenance(self):
        e = element(); e['outcome']['record']['cells'][0]['raw_value'] = 'Distance'
        d, first, issue = finding_entry(e, '/record/cells/0/raw_value')
        second = resolution(first, issue, 'Distance (angstrom)')
        view = reviews.apply(d, [first, second])[0]
        text = register(view)
        for value in (issue['id'], 'resolved-with-attribution', 'Distance (angstrom)', 'reviewer-one', 'source-inspection'):
            self.assertIn(value, text)

    def test_matching_and_answer_stage_resolutions_allow_scoped_exact_use(self):
        for stage in ('extraction', 'answer'):
            with self.subTest(stage=stage):
                e = element(); target = '/record/cells/0/raw_value'
                d, first, issue = finding_entry(e, target, stage=stage)
                second = resolution(first, issue, 'Distance (angstrom)', basis='literal-copy')
                cover(second, e, target)
                view = reviews.apply(d, [first, second])[0]
                result = exports.exact_view(view, target, purpose='exact')
                self.assertEqual(result['content'], 'Distance (angstrom)')
                self.assertEqual(result['unresolved_findings'], [])
                self.assertIn(issue['id'], json.dumps(result))
                self.assertIn(stage, register(view))


class ResolutionEvidence(unittest.TestCase):
    def test_native_literal_cannot_resolve_any_automatic_saved_issue(self):
        states = [dict(grouping='unresolved'), dict(indent=None, layout_version='native-layout-v2'),
                  dict(layout_uncertainties=['Synthetic layout uncertainty']),
                  dict(unresolved_symbols=['Synthetic notation uncertainty']),
                  dict(header_status='unresolved'), dict(status='partial', grouping='unresolved')]
        for state in states:
            with self.subTest(state=state):
                e = element(); line = copy.deepcopy(e['outcome']['record']['cells'][0])
                line.update(text=line.pop('raw_value'), **state)
                e['outcome']['record'] = dict(kind='algorithm', lines=[line])
                d, first = setup_review(e)
                issue = next(f for f in project(e)['findings'] if f['target'] == '/record/lines/0')
                second = resolution(first, issue, 'Distance (angstrom)', basis='literal-copy', aspect='content')
                with self.assertRaisesRegex(ValueError, 'saved-uncertainty-requires-source-inspection'):
                    reviews.apply(d, [second])

    def test_single_aspect_crop_cannot_clear_compound_saved_issue(self):
        e = element(); target = '/record/cells/0'
        e['outcome']['record']['cells'][0].update(status='partial', grouping='unresolved')
        d, first = setup_review(e); issue = project(e)['findings'][0]
        second = resolution(first, issue, e['outcome']['record']['cells'][0], aspect='content')
        view = reviews.apply(d, [second])[0]
        actual = next(f for f in view['findings'] if f['id'] == issue['id'])
        self.assertEqual(actual['status'], 'unresolved')
        self.assertEqual(len(actual['resolutions']), 1)
        self.assertIn(issue['id'], json.dumps(exports.exact_view(view, target)))
        self.assertIn('unresolved', register(view))
        self.assertEqual(exports.exact_view(view, '/record/cells/1/raw_value')['content'], '3.0')

    def test_complete_attributed_inspection_is_representable_without_edits(self):
        e = element(); target = '/record/cells/0'
        e['outcome']['record']['cells'][0].update(status='partial', grouping='unresolved')
        before = digest(e); d, first = setup_review(e); issue = project(e)['findings'][0]
        decisions = [resolution(first, issue, copy.deepcopy(e['outcome']['record']['cells'][0]), aspect=a)
                     for a in reviews.ASPECTS]
        cover(decisions[-1], e, target)
        view = reviews.apply(d, decisions)[0]
        self.assertEqual(view['findings'][0]['status'], 'resolved-with-attribution')
        self.assertEqual(len(view['findings'][0]['resolutions']), len(reviews.ASPECTS))
        self.assertEqual(exports.exact_view(view, target, purpose='exact')['content'], e['outcome']['record']['cells'][0])
        self.assertEqual(digest(e), before)


class ResolutionConflicts(unittest.TestCase):
    def test_different_proposals_stay_unresolved_in_both_orders(self):
        for readings in (('Distance (angstrom)', 'Distance (nm)'), ('Distance (nm)', 'Distance (angstrom)')):
            with self.subTest(readings=readings):
                e = element(); d, first, issue = finding_entry(e, '/record/cells/0/raw_value')
                decisions = [first] + [resolution(first, issue, reading, identity='reviewer-'+str(i))
                                       for i, reading in enumerate(readings)]
                view = reviews.apply(d, decisions)[0]
                actual = view['findings'][0]
                self.assertEqual(actual['status'], 'unresolved')
                self.assertEqual([r['proposed_value'] for r in actual['resolutions']], list(readings))
                for target in ('/record/cells/0/raw_value', '/record/cells/0', '/record'):
                    consumer = exports.exact_view(view, target)
                    self.assertIn(issue['id'], [f['id'] for f in consumer['unresolved_findings']])
                    for reading in readings: self.assertIn(reading, json.dumps(consumer))
                text = register(view)
                for value in (*readings, 'reviewer-0', 'reviewer-1', 'unresolved'): self.assertIn(value, text)

    def test_identical_values_agree_but_types_and_uncertain_equivalence_do_not(self):
        for left, right, expected in [('Distance (angstrom)', 'Distance (angstrom)', 'resolved-with-attribution'),
                                      (1, True, 'unresolved'), (1, 1.0, 'unresolved'),
                                      ('1 nm', '10 angstrom', 'unresolved')]:
            with self.subTest(left=left, right=right):
                d, first, issue = finding_entry(element(), '/record/cells/0/raw_value')
                view = reviews.apply(d, [first, resolution(first, issue, left),
                                        resolution(first, issue, right, identity='reviewer-two')])[0]
                self.assertEqual(view['findings'][0]['status'], expected)
                self.assertEqual(len(view['findings'][0]['resolutions']), 2)

    def test_parent_child_and_separate_findings_cannot_hide_conflicts(self):
        for mode in ('same-target', 'parent-child', 'uncomparable-parent'):
            for reverse in (False, True):
                with self.subTest(mode=mode, reverse=reverse):
                    e = element(); target = '/record/cells/0/raw_value'
                    parent = '/record/cells/0' if mode != 'same-target' else target
                    d, first, issue = finding_entry(e, parent)
                    second_finding = copy.deepcopy(first)
                    second_finding['submission']['findings'][0].update(target=target, reason='Synthetic independent second issue.')
                    other = reviews.apply(d, [first, second_finding])[0]['findings'][-1]
                    proposed = copy.deepcopy(e['outcome']['record']['cells'][0]) if mode == 'parent-child' else 'Distance (angstrom)'
                    decisions = [resolution(first, issue, proposed), resolution(first, other, 'Distance (nm)', identity='reviewer-two')]
                    if reverse: decisions.reverse()
                    view = reviews.apply(d, [first, second_finding, *decisions])[0]
                    self.assertTrue(all(f['status'] == 'unresolved' for f in view['findings']))
                    consumer = exports.exact_view(view, '/record/cells/0')
                    self.assertEqual({f['id'] for f in consumer['unresolved_findings']}, {issue['id'], other['id']})
                    self.assertIn('Distance (nm)', register(view))

    def test_matching_parent_child_and_disjoint_scopes_are_not_conflicts(self):
        for target in ('/record/cells/0/raw_value', '/record/cells/1/raw_value'):
            with self.subTest(target=target):
                e = element(); d, first, issue = finding_entry(e, '/record/cells/0')
                second_finding = copy.deepcopy(first)
                second_finding['submission']['findings'][0].update(target=target, reason='Synthetic separately scoped issue.')
                other = reviews.apply(d, [first, second_finding])[0]['findings'][-1]
                proposed = 'Distance (angstrom)' if '/0/' in target else '3.0'
                decisions = [first, second_finding, resolution(first, issue, e['outcome']['record']['cells'][0]),
                             resolution(first, other, proposed, identity='reviewer-two')]
                view = reviews.apply(d, decisions)[0]
                self.assertTrue(all(f['status'] == 'resolved-with-attribution' for f in view['findings']))

    def test_native_evidence_and_newer_proposal_do_not_override_crop_reading(self):
        d, first, issue = finding_entry(element(), '/record/cells/0/raw_value')
        decisions = [first, resolution(first, issue, 'Distance (nm)'),
                     resolution(first, issue, 'Distance (angstrom)', basis='literal-copy', identity='native-reviewer')]
        view = reviews.apply(d, decisions)[0]
        self.assertEqual(view['findings'][0]['status'], 'unresolved')
        self.assertEqual(len(view['findings'][0]['resolutions']), 2)


if __name__ == '__main__':
    sys.addaudithook(lambda event, args: (_ for _ in ()).throw(RuntimeError('offline-network-blocked')) if event.startswith('socket.') else None)
    unittest.main(verbosity=2)
