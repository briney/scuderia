"""Offline test suite for the enrichment stage.

Driver: run_tests.py. These tests exercise:
  - real-package preparation and read-back (current consolidated package),
  - the explicit historical adapter,
  - figure evidence separation/schema/source refs,
  - table headers/spans/lexical fidelity/native-copy/blank-vs-unknown/raster provenance,
  - algorithm ordering/indentation/operators,
  - multipage ordering, embedded-table parent links (association-level),
  - unresolved input, invalid/missing/truncated model outputs,
  - exact element accounting,
  - unsafe output reuse / path escape,
  - input mutation detection,
  - no live calls during offline tests (socket audit hook).
"""
import copy
import json
import os
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
PKG = HERE.parents[1]
sys.path.insert(0, str(PKG))
from pdf_enrichment import io as pe_io, package_io, requests as pe_requests, schema, tables, algorithms
from pdf_enrichment import accounting, importer, copy_rules, review as review_mod

FIXTURES = Path(os.environ['PDF_ENRICHMENT_FIXTURES'])
CURRENT_PACKAGE = FIXTURES / 'current'
HIST_PACKAGE = FIXTURES / 'historical'

from pdf_enrichment.io import offline as install_offline
install_offline()


def fig_response(evidence=None):
    ev=evidence or evidence_with_lines()
    ref=ev['captions'][0]['region_id'] if ev.get('caption_only') else ev['body_fragments'][0]['fragment_id']
    basis='caption-text' if ev.get('caption_only') else 'crop-image'
    return {'shown':{'panels':[{'id':'a','text':'Synthetic panel description.','basis':basis,'source_ref':ref}]},
            'observations':[{'panel':'a','panel_ref':'a','text':'Synthetic mechanics observation.','source_ref':ref,'evidence_basis':basis}],
            'caption_context':{'summary':{'text':'Synthetic caption context.','basis':'caption-text','source_ref':ev['captions'][0]['region_id']}},
            'limitations':[],
            'coverage':dict(scope='caption-only' if ev.get('caption_only') else 'image-plus-caption',
                            status='complete',gaps=[],source_refs=[c['region_id'] for c in ev['captions']]+([] if ev.get('caption_only') else [f['fragment_id'] for f in ev['body_fragments']]))}


def table_response():
    value = {
        "status": "ok",
        "rows": [{"index": 0, "span_from": None, "span_to": None}, {"index": 1, "span_from": None, "span_to": None},
                 {"index": 2, "span_from": None, "span_to": None}],
        "columns": [{"index": 0, "span_from": None, "span_to": None}, {"index": 1, "span_from": None, "span_to": None},
                    {"index": 2, "span_from": None, "span_to": None}],
        "cells": [
            {"row": 0, "column": 0, "row_span": 1, "col_span": 2, "raw_value": None,
             "native_line_ids": ["L1"], "raster_text": None, "blank": False, "unreadable": False,
             "unresolved": False, "notes": None},
            {"row": 0, "column": 2, "row_span": 1, "col_span": 1, "raw_value": None,
             "native_line_ids": [], "raster_text": "007", "blank": False, "unreadable": False,
             "unresolved": False, "notes": None},
            {"row": 1, "column": 0, "row_span": 1, "col_span": 1, "raw_value": None,
             "native_line_ids": ["L2"], "raster_text": None, "blank": False, "unreadable": False,
             "unresolved": False, "notes": None},
            {"row": 1, "column": 1, "row_span": 1, "col_span": 1, "raw_value": None,
             "native_line_ids": [], "raster_text": None, "blank": True, "unreadable": False,
             "unresolved": False, "notes": None},
            {"row": 1, "column": 2, "row_span": 1, "col_span": 1, "raw_value": None,
             "native_line_ids": [], "raster_text": None, "blank": False, "unreadable": False,
             "unresolved": True, "notes": None},
            {"row": 2, "column": 0, "row_span": 1, "col_span": 1, "raw_value": None,
             "native_line_ids": ["L3"], "raster_text": None, "blank": False, "unreadable": False,
             "unresolved": False, "notes": None},
            {"row": 2, "column": 1, "row_span": 1, "col_span": 1, "raw_value": None,
             "native_line_ids": [], "raster_text": None, "blank": False, "unreadable": True,
             "unresolved": False, "notes": None},
            {"row": 2, "column": 2, "row_span": 1, "col_span": 1, "raw_value": None,
             "native_line_ids": [], "raster_text": "<0.01", "blank": False, "unreadable": False,
             "unresolved": False, "notes": None}],
        "header_hierarchy": {"0,0": ["0,1"]},
        "units": [{"column": 2, "unit": "ms", "basis": "caption-text"}],
        "caption_markers": [{"marker": "*", "basis": "native-text", "caption_text": "p < 0.01 (printed)"}],
        "unresolved": [{"kind": "cell", "ref": "row:1,column:2", "reason": "illegible in crop"}]}
    value['header_hierarchy']={'0,2':['0,0']}
    for c in value['cells']: c['source_refs']=['f1']
    value['units'][0]['source_ref']='r1'
    value['caption_markers'][0]['source_ref']='L1'
    return value


def algo_response():
    value = {
        "status": "ok", "title": "Algorithm 6 Policy iteration",
        "inputs": [{"name": "M", "description": "model", "line_refs": [], "basis": "native-text"}],
        "outputs": [{"name": "π*", "description": None, "line_refs": [], "basis": "crop-image"}],
        "lines": [
            {"line_number": 1, "line_number_printed": True, "indent": 0, "text": "initialize π₀ ← random policy",
             "comment": None, "native_line_ids": [], "basis": "crop-image"},
            {"line_number": 2, "line_number_printed": True, "indent": 1, "text": "repeat",
             "comment": None, "native_line_ids": [], "basis": "crop-image"},
            {"line_number": 3, "line_number_printed": True, "indent": 1, "text": "V ← V + α·δ  # errror kept",
             "comment": "errror kept", "native_line_ids": [], "basis": "crop-image"}],
        "unresolved_symbols": ["δ"],
        "apparent_typos": [{"line_number": 3, "text": "errror kept", "note": "apparent-typo-preserved"}]}
    value['inputs'][0]['line_refs']=['L1']
    value['outputs'][0]['line_refs']=['f1']
    for line in value['lines']: line['source_refs']=['f1']
    return value


def evidence_with_lines():
    return {"element_id": "e::elem", "label": "Table S1",
            "body_fragments": [{"fragment_id": "f1", "page": 74, "bbox": [0, 0, 100, 100], "crop": "x.png",
                                 "crop_sha256": None,
                                 "native_lines": [
                                     dict(line_id="L1", page=74, bbox=[0, 0, 10, 4], text="Params n layers"),
                                     dict(line_id="L2", page=74, bbox=[0, 5, 10, 9], text="1.4B"),
                                     dict(line_id="L3", page=74, bbox=[0, 10, 10, 14], text="±0.05")]}],
            "captions": [dict(candidate_id="c1", region_id="r1", page=74, bbox=[0, 20, 100, 30],
                               crop="cap.png", crop_sha256=None, native_text="Table S1.",
                               lines=[dict(line_id="L9", text="Table S1.", bbox=[0, 20, 50, 25])])]}


class SocketBlockTest(unittest.TestCase):
    def test_socket_blocked(self):
        import socket
        with self.assertRaises(RuntimeError):
            socket.create_connection(('127.0.0.1', 80), timeout=0.2)


class RealPackagePrepareTest(unittest.TestCase):
    """Real current package: prepare, read back, immutability."""

    @classmethod
    def setUpClass(cls):
        cls.scratch = Path(os.environ.get('PDF_ENRICHMENT_TEST_SCRATCH', HERE / 'scratch'))
        cls.run_dir = cls.scratch / 'current-run'
        if cls.run_dir.exists():
            raise unittest.SkipTest('scratch reuse forbidden')
        cls.pkg_before = package_io.SourcePackage(CURRENT_PACKAGE)
        cls.plan = pe_requests.prepare(CURRENT_PACKAGE, cls.run_dir, kinds=['figure'])
        cls.pkg_after = package_io.SourcePackage(CURRENT_PACKAGE)

    def test_source_package_unchanged(self):
        self.assertEqual(self.pkg_before.snapshot['tree_sha256'], self.pkg_after.snapshot['tree_sha256'])

    def test_plan_requests_match_elements(self):
        figs = [r for r in self.plan['requests'] if r.get('kind') == 'figure']
        self.assertEqual(len(figs), 6)

    def test_request_bindings_present(self):
        for row in self.plan['requests']:
            if row.get('kind') is None:
                continue
            self.assertTrue(row['request_sha256'])
            self.assertTrue(row['source_package_tree_sha256'])
            self.assertTrue(row['source_sha256'])
            self.assertEqual(row['model'], 'qwen3.8-27b')

    def test_readback_wire_and_evidence(self):
        for row in self.plan['requests']:
            if row.get('kind') is None:
                continue
            wire = pe_io.load(self.run_dir / row['directory'] / 'request-wire.json')
            self.assertEqual(wire['model'], 'qwen3.8-27b')
            self.assertEqual(pe_io.sha(self.run_dir / row['directory'] / 'request-wire.json'), row['request_sha256'])
            ev = pe_io.load(self.run_dir / row['directory'] / 'source-evidence.json')
            self.assertEqual(ev['element_id'], row['element_id'])
            self.assertTrue(ev['body_fragments'])
            self.assertTrue(ev['captions'])

    def test_figure_request_contains_crops_and_caption(self):
        row = next(r for r in self.plan['requests'] if r.get('kind') == 'figure')
        wire = pe_io.load(self.run_dir / row['directory'] / 'request-wire.json')
        parts = wire['messages'][0]['content']
        imgs = [p for p in parts if p['type'] == 'image_url']
        self.assertGreaterEqual(len(imgs), 2)  # body fragment + caption
        text = parts[0]['text']
        self.assertIn('SOURCE EVIDENCE', text)
        self.assertIn(row['element_id'], text)

    def test_execute_requires_approval_argument(self):
        from pdf_enrichment import cli
        with self.assertRaises(SystemExit):
            cli.main(['execute', '--run', 'x'])


class HistoricalAdapterTest(unittest.TestCase):
    def test_historical_elements_load(self):
        pkg = package_io.SourcePackage(HIST_PACKAGE)
        self.assertTrue(pkg.historical)
        tables_n = sum(1 for d in pkg.documents for e in d['elements'] if e['content_type'] == 'table')
        algos_n = sum(1 for d in pkg.documents for e in d['elements'] if e['content_type'] == 'algorithm')
        self.assertEqual(tables_n, 21)  # 17 (hayes) + 4 (rfdiffusion2)
        self.assertEqual(algos_n, 18)    # 13 (hayes) + 5 (rfdiffusion2)

    def test_historical_prepare_tables(self):
        scratch = Path(os.environ.get('PDF_ENRICHMENT_TEST_SCRATCH', HERE / 'scratch'))
        run = scratch / 'hist-table-run'
        if run.exists():
            raise unittest.SkipTest('scratch reuse forbidden')
        plan = pe_requests.prepare(HIST_PACKAGE, run, kinds=['table'])
        kinds = [r.get('kind') for r in plan['requests']]
        self.assertEqual(kinds.count('table'), 21)

    def test_historical_manifest_schema_flagged(self):
        pkg = package_io.SourcePackage(HIST_PACKAGE)
        self.assertNotEqual(pkg.schema, 'pdf-source-package-v1')


class FigureSchemaTest(unittest.TestCase):
    def test_valid(self):
        schema.validate_figure(fig_response(), evidence_with_lines())

    def test_missing_key_rejected(self):
        v = fig_response(); del v['limitations']
        with self.assertRaises(ValueError):
            schema.validate_figure(v, evidence_with_lines())

    def test_extra_key_rejected(self):
        v = fig_response(); v['extra'] = 1
        with self.assertRaises(ValueError):
            schema.validate_figure(v, evidence_with_lines())

    def test_observation_needs_source_ref(self):
        v = fig_response(); v['observations'][0]['source_ref'] = None
        with self.assertRaises(ValueError):
            schema.validate_figure(v, evidence_with_lines())

    def test_unknown_basis_rejected(self):
        v = fig_response(); v['observations'][0]['evidence_basis'] = 'guess'
        with self.assertRaises(ValueError):
            schema.validate_figure(v, evidence_with_lines())


class TableSchemaTest(unittest.TestCase):
    def test_valid(self):
        schema.validate_table(table_response())

    def test_missing_truncated_rejected(self):
        v = table_response(); del v['cells']
        with self.assertRaises(ValueError):
            schema.validate_table(v)

    def test_raw_value_from_model_rejected(self):
        v = table_response(); v['cells'][1]['raw_value'] = 'invented'
        with self.assertRaises(ValueError):
            schema.validate_table(v)

    def test_blank_with_content_rejected(self):
        v = table_response(); v['cells'][3]['native_line_ids'] = ['L2']
        with self.assertRaises(ValueError):
            schema.validate_table(v)

    def test_unknown_native_line_rejected(self):
        v = table_response(); v['cells'][0]['native_line_ids'] = ['NOPE']
        ev = evidence_with_lines()
        with self.assertRaises(ValueError):
            tables.assemble(ev, v)

    def test_duplicate_grid_slot_rejected(self):
        v = table_response()
        v['cells'].append(copy.deepcopy(v['cells'][1]))
        v['cells'][-1]['native_line_ids'] = []
        v['cells'][-1]['raster_text'] = None
        v['cells'][-1]['unresolved'] = True
        with self.assertRaises(ValueError):
            tables.assemble(evidence_with_lines(), v)


class TableAssemblyTest(unittest.TestCase):
    def test_native_copy_joins_literal_strings(self):
        v = table_response()
        rec = tables.assemble(evidence_with_lines(), v)
        cell = rec['cells'][0]
        self.assertEqual(cell['raw_value'], 'Params n layers')
        self.assertEqual(cell['status'], 'native')
        self.assertEqual(cell['provenance'], 'native-copy:line-granular')

    def test_no_numeric_coercion(self):
        ev = evidence_with_lines()
        v = table_response()
        rec = tables.assemble(ev, v)
        vals = [c['raw_value'] for c in rec['cells'] if c['status'] == 'native']
        self.assertIn('±0.05', vals)
        self.assertIn('1.4B', vals)

    def test_raster_provenance(self):
        rec = tables.assemble(evidence_with_lines(), table_response())
        raster = [c for c in rec['cells'] if c['status'] == 'raster']
        self.assertEqual(raster[0]['raw_value'], '007')
        self.assertIn('raster-transcription', raster[0]['provenance'])

    def test_blank_vs_unreadable_vs_unresolved_distinct(self):
        rec = tables.assemble(evidence_with_lines(), table_response())
        by = {c['status'] for c in rec['cells']}
        self.assertIn('blank', by); self.assertIn('unresolved', by)
        self.assertEqual([c for c in rec['cells'] if c['status'] == 'blank'][0]['raw_value'], '')
        self.assertIsNone([c for c in rec['cells'] if c['status'] == 'unresolved'][0]['raw_value'])

    def test_span_accounted_in_grid(self):
        rec = tables.assemble(evidence_with_lines(), table_response())
        c0 = rec['cells'][0]
        self.assertEqual((c0['row_span'], c0['col_span']), (1, 2))

    def test_header_hierarchy_preserved(self):
        rec = tables.assemble(evidence_with_lines(), table_response())
        self.assertEqual(rec['header_hierarchy'], {"0,2": ["0,0"]})

    def test_csv_only_if_rectangular(self):
        rec = tables.assemble(evidence_with_lines(), table_response())
        with self.assertRaises(ValueError):
            tables.export_csv(rec)

    def test_csv_export_when_rectangular(self):
        v = table_response()
        # Make every slot a single 1x1 cell with bound content (native or raster).
        v['cells'][0]['col_span'] = 1
        v['cells'] = [c for c in v['cells']
                     if not (c['blank'] or c['unreadable'] or c['unresolved'])]
        v['cells'].append({"row": 0, "column": 1, "row_span": 1, "col_span": 1, "raw_value": None,
                           "native_line_ids": ["L2"], "raster_text": None, "blank": False,
                           "unreadable": False, "unresolved": False, "notes": None})
        v['cells'].append({"row": 1, "column": 1, "row_span": 1, "col_span": 1, "raw_value": None,
                           "native_line_ids": ["L3"], "raster_text": None, "blank": False,
                           "unreadable": False, "unresolved": False, "notes": None})
        v['cells'].append({"row": 1, "column": 2, "row_span": 1, "col_span": 1, "raw_value": None,
                           "native_line_ids": [], "raster_text": "ND", "blank": False,
                           "unreadable": False, "unresolved": False, "notes": None})
        v['cells'].append({"row": 2, "column": 1, "row_span": 1, "col_span": 1, "raw_value": None,
                           "native_line_ids": [], "raster_text": "1.5E-3", "blank": False,
                           "unreadable": False, "unresolved": False, "notes": None})
        v['unresolved'] = []
        for cell in v['cells']: cell['source_refs']=['f1']
        # Disjoint slices of the same source line preserve lexical coverage without duplicating it.
        v['cells'][-4].update(native_line_ids=[],native_refs=[dict(line_id='L2',start=0,end=1)])
        v['cells'][2].update(native_line_ids=[],native_refs=[dict(line_id='L2',start=1,end=4)])
        v['cells'][-3].update(native_line_ids=[],native_refs=[dict(line_id='L3',start=0,end=1)])
        v['cells'][3].update(native_line_ids=[],native_refs=[dict(line_id='L3',start=1,end=5)])
        rec = tables.assemble(evidence_with_lines(), v)
        self.assertTrue(tables.rectangular_dense(rec))
        csv_text, meta = tables.export_csv(rec)
        self.assertIn('007', csv_text)
        self.assertIn('<0.01', csv_text)
        self.assertIn('ND', csv_text)
        self.assertIn('1.5E-3', csv_text)

    def test_shared_native_line_warned(self):
        # v3 strengthens the former warning into rejection of overlapping source ranges.
        v = table_response()
        v['cells'][2]['native_line_ids'] = ['L1']
        with self.assertRaisesRegex(ValueError,'overlapping-native-ranges'):
            tables.assemble(evidence_with_lines(), v)


class AlgorithmTest(unittest.TestCase):
    def test_valid(self):
        schema.validate_algorithm(algo_response())

    def test_printed_labels_do_not_reorder_lines(self):
        v = algo_response(); v['lines'][1]['line_number'] = 5
        record=algorithms.assemble(evidence_with_lines(), v)
        self.assertEqual([l['line_number'] for l in record['lines']],[1,5,3])

    def test_source_indentation_jump_preserved(self):
        v = algo_response(); v['lines'][1]['indent'] = 3
        record=algorithms.assemble(evidence_with_lines(), v)
        self.assertEqual(record['lines'][1]['indent'],3)

    def test_symbols_preserved(self):
        rec = algorithms.assemble(evidence_with_lines(), algo_response())
        texts = [l['text'] for l in rec['lines']]
        self.assertTrue(any('π₀' in t for t in texts))
        self.assertTrue(any('α·δ' in t for t in texts))

    def test_typo_preserved_and_flagged(self):
        rec = algorithms.assemble(evidence_with_lines(), algo_response())
        self.assertTrue(any('errror' in l['text'] for l in rec['lines']))
        self.assertEqual(rec['apparent_typos'][0]['line_number'], 3)

    def test_printed_line_numbers(self):
        rec = algorithms.assemble(evidence_with_lines(), algo_response())
        self.assertEqual([l['line_number'] for l in rec['lines']], [1, 2, 3])
        rendered = algorithms.render_text(rec)
        self.assertIn('initialize π₀', rendered)

    def test_missing_line_rejected(self):
        v = algo_response(); v['lines'] = []
        with self.assertRaises(ValueError):
            algorithms.assemble(evidence_with_lines(), v)


class MultipageAndEmbeddedTest(unittest.TestCase):
    def test_multipage_element_fragments_ordered(self):
        pkg = package_io.SourcePackage(HIST_PACKAGE)
        # find any element with fragments spanning multiple pages
        multi = [e for d in pkg.documents for e in d['elements']
                 if len({f['page'] for f in e['ordered_source_fragments']}) > 1]
        if not multi:
            self.skipTest('no multipage element in this package')
        e = multi[0]
        pages = [f['page'] for f in e['ordered_source_fragments']]
        self.assertEqual(pages, sorted(pages))

    def test_embedded_table_stays_linked_to_parent_figure(self):
        ev=evidence_with_lines(); value=fig_response(ev)
        value['embedded_tables']=[dict(id='embedded-1',source_refs=['f1'],table=table_response())]
        record=importer._record_for('figure',ev,value)
        self.assertEqual(len(record['embedded_tables']),1)
        child=record['embedded_tables'][0]
        self.assertEqual(child['parent_element_id'],ev['element_id'])
        self.assertFalse(child['standalone'])
        self.assertEqual(child['cells'][1]['raw_value'],'007')


class AccountingTest(unittest.TestCase):
    def test_exact_accounting(self):
        plan = dict(requests=[dict(element_id='e1', document='d', kind='figure', id='r1', status='prepared-not-sent')])
        acct = accounting.accounting(plan, {})
        self.assertEqual(acct['total_elements_accounted'], 1)
        self.assertEqual(acct['elements'][0]['status'], 'prepared-not-sent')

    def test_failed_disposition(self):
        plan = dict(requests=[dict(element_id='e1', document='d', kind='table', id='r1')])
        acct = accounting.accounting(plan, {'r1': dict(status='failed', reason='schema-rejection:x')})
        self.assertEqual(acct['elements'][0]['status'], 'failed')
        self.assertFalse(acct['elements'][0].get('complete'))

    def test_unknown_type_visible(self):
        plan = dict(requests=[dict(element_id='eX', document='d', kind=None, status='kind-not-selected')])
        acct = accounting.accounting(plan, {})
        self.assertEqual(acct['elements'][0]['status'], 'not-selected')
        self.assertTrue(acct['elements'][0]['not_proof_of_absence'])


class UnsafePathTest(unittest.TestCase):
    def test_path_escape_rejected(self):
        run = Path(os.environ.get('PDF_ENRICHMENT_TEST_SCRATCH', HERE / 'scratch'))
        run.mkdir(parents=True, exist_ok=True)
        with self.assertRaises(ValueError):
            pe_io.safe(run, '../escape.json')

    def test_output_reuse_rejected(self):
        run = Path(os.environ.get('PDF_ENRICHMENT_TEST_SCRATCH', HERE / 'scratch')) / 'reuse-run'
        if run.exists():
            raise unittest.SkipTest('scratch reuse forbidden')
        pe_requests.prepare(CURRENT_PACKAGE, run, kinds=['figure'])
        with self.assertRaises(ValueError):
            pe_requests.prepare(CURRENT_PACKAGE, run, kinds=['figure'])

    def test_response_reimport_rejected(self):
        run = Path(os.environ.get('PDF_ENRICHMENT_TEST_SCRATCH', HERE / 'scratch')) / 'import-run'
        if run.exists():
            raise unittest.SkipTest('scratch reuse forbidden')
        plan = pe_requests.prepare(CURRENT_PACKAGE, run, kinds=['figure'])
        row = next(r for r in plan['requests'] if r.get('kind') == 'figure')
        resp = {row['id']: {"content": json.dumps(fig_response(pe_io.load(run / row['directory'] / 'source-evidence.json')))}}
        resp_path = run.parent / 'synthetic-responses.json'
        pe_io.save(resp_path, resp)
        importer.import_test_response(run, resp_path, row['id'])
        with self.assertRaises(ValueError):
            importer.import_test_response(run, resp_path, row['id'])


class ImportTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.scratch = Path(os.environ.get('PDF_ENRICHMENT_TEST_SCRATCH', HERE / 'scratch'))
        cls.run_dir = cls.scratch / 'import-full-run'
        if cls.run_dir.exists():
            raise unittest.SkipTest('scratch reuse forbidden')
        cls.plan = pe_requests.prepare(CURRENT_PACKAGE, cls.run_dir, kinds=['figure'])
        cls.rows = [r for r in cls.plan['requests'] if r.get('kind') == 'figure']

    def test_import_and_report(self):
        resp = {r['id']: {"content": json.dumps(fig_response(pe_io.load(self.run_dir / r['directory'] / 'source-evidence.json')))} for r in self.rows}
        path = self.scratch / 'fig-responses.json'
        pe_io.save(path, resp)
        importer.import_test_response(self.run_dir, path)
        state = importer.report(self.run_dir)
        self.assertTrue(state['selected_mechanics_complete'])
        self.assertFalse(state['requested_work_complete'])
        self.assertFalse(state['production_complete'])
        self.assertTrue(state['contains_synthetic_responses'])
        self.assertTrue((self.run_dir / 'review.html').exists())
        html = (self.run_dir / 'review.html').read_text()
        self.assertIn('SYNTHETIC TEST RESPONSE', html)
        self.assertIn(os.path.relpath(CURRENT_PACKAGE, self.run_dir), html)
        self.assertIn('<img', html)

    def test_invalid_response_recorded_as_failed(self):
        run = self.scratch / 'import-bad-run'
        if run.exists():
            raise unittest.SkipTest('scratch reuse forbidden')
        plan = pe_requests.prepare(CURRENT_PACKAGE, run, kinds=['figure'])
        row = next(r for r in plan['requests'] if r.get('kind') == 'figure')
        bad = {row['id']: {"content": json.dumps({"shown": {}})}}  # truncated
        path = self.scratch / 'bad-responses.json'
        pe_io.save(path, bad)
        with self.assertRaises(ValueError):
            importer.import_test_response(run, path, row['id'])
        results = pe_io.load(run / 'enrichment-results.json')
        self.assertEqual(results['responses'][row['id']]['status'], 'failed')
        state = importer.report(run)
        self.assertFalse(state['requested_work_complete'])

    def test_report_before_import_shows_pending(self):
        run = self.scratch / 'pending-run'
        if run.exists():
            raise unittest.SkipTest('scratch reuse forbidden')
        pe_requests.prepare(CURRENT_PACKAGE, run, kinds=['figure'])
        state = importer.report(run)
        self.assertFalse(state['requested_work_complete'])
        self.assertEqual(state['accounting']['elements'][0]['status'], 'prepared-not-sent')


class InputMutationTest(unittest.TestCase):
    def test_source_package_hash_stable_across_prepare(self):
        scratch = Path(os.environ.get('PDF_ENRICHMENT_TEST_SCRATCH', HERE / 'scratch'))
        before = package_io.SourcePackage(CURRENT_PACKAGE).snapshot['tree_sha256']
        run = scratch / 'mutation-run'
        if run.exists():
            raise unittest.SkipTest('scratch reuse forbidden')
        pe_requests.prepare(CURRENT_PACKAGE, run, kinds=['figure'])
        after = package_io.SourcePackage(CURRENT_PACKAGE).snapshot['tree_sha256']
        self.assertEqual(before, after)


class CliTest(unittest.TestCase):
    def test_cli_prepare_and_report(self):
        scratch = Path(os.environ.get('PDF_ENRICHMENT_TEST_SCRATCH', HERE / 'scratch'))
        run = scratch / 'cli-run'
        if run.exists():
            raise unittest.SkipTest('scratch reuse forbidden')
        from pdf_enrichment import cli
        rc = cli.main(['--offline', 'prepare', '--source-package', str(CURRENT_PACKAGE),
                       '--output', str(run), '--kinds', 'figure', '--fixture'])
        self.assertEqual(rc, 0)
        plan = pe_io.load(run / 'enrichment-plan.json')
        figs = [r for r in plan['requests'] if r.get('kind') == 'figure']
        row = figs[0]
        resp = {row['id']: {"content": json.dumps(fig_response(pe_io.load(run / row['directory'] / 'source-evidence.json')))}}
        pe_io.save(scratch / 'cli-responses.json', resp)
        rc = cli.main(['--offline', 'import-test-response', '--run', str(run),
                       '--responses', str(scratch / 'cli-responses.json')])
        self.assertEqual(rc, 0)
        rc = cli.main(['--offline', 'report', '--run', str(run)])
        self.assertEqual(rc, 0)


class CaptionOnlyVariantTest(unittest.TestCase):
    def test_caption_only_marked_and_imageless(self):
        scratch = Path(os.environ.get('PDF_ENRICHMENT_TEST_SCRATCH', HERE / 'scratch'))
        run = scratch / 'caption-only-run'
        if run.exists():
            raise unittest.SkipTest('scratch reuse forbidden')
        plan = pe_requests.prepare(CURRENT_PACKAGE, run, kinds=['figure'], caption_only=True)
        row = next(r for r in plan['requests'] if r.get('kind') == 'figure')
        self.assertTrue(row['caption_only'])
        wire = pe_io.load(run / row['directory'] / 'request-wire.json')
        parts = wire['messages'][0]['content']
        self.assertTrue(all(p['type'] == 'text' for p in parts))
        self.assertIn('CAPTION-ONLY INPUT VARIANT', parts[0]['text'])
        self.assertTrue(plan['caption_only_variant'])


if __name__ == '__main__':
    unittest.main(verbosity=2)
