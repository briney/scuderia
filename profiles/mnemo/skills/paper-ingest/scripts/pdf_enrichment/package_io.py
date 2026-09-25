"""Read-only loading of saved source packages.

A SourcePackage binds:
  - the package root (immutable; never written to),
  - per-document identity, raw PDF path + sha256,
  - logical elements with ordered source fragments, crops, lines, labels,
  - per-document candidates (native_text, observed labels, regions),
  - per-page native line index (for table native-copy binding).

Supports the CURRENT schema by recomputing the accepted read-only workflow's
final_state from current evidence, never trusting cached results.json. The
EXPLICIT historical adapter (offline-saved-response-document-update-v1) has a
different manifest and is not fed to current final_state. Historical records
are pilot evidence only; source gaps and limitations remain in document metadata.
"""
from pathlib import Path
from .io import require, load, sha, tree_hash, safe
from . import trusted


class SourcePackage:
    def __init__(self, root, method=None):
        self.method = trusted.method_path(method)
        self.root = Path(root).absolute()
        require(self.root.is_dir(), 'package-root-missing')
        self.manifest = load(self.root / 'manifest.json')
        self.schema = self.manifest.get('schema')
        self.historical = self.schema == 'offline-saved-response-document-update-v1'
        self.snapshot = tree_hash(self.root)
        self.documents = []
        self._candidates = {}
        if self.historical:
            self._load_historical()
        else:
            self._load_current()
        require(len({d['identity'] for d in self.documents})==len(self.documents),'duplicate-source-document')
        for doc in self.documents:
            require(all(e['source_document']==doc['identity'] for e in doc['elements']),'element-document-mismatch')

    # ---------- current schema ----------

    def _load_current(self):
        require(self.schema == 'pdf-source-package-v1', 'unsupported-package-schema:' + str(self.schema))
        # Validate paths before the accepted read-only workflow opens inputs.
        for doc in self.manifest['documents']:
            safe(self.root,doc['raw'])
            for page in doc['pages']:
                for key in ('directory','native_text','page_image'):
                    if page.get(key): safe(self.root,page[key])
        for phase in ('initial','classification','association'):
            p=self.root/(phase+'-plan.json')
            if not p.exists(): continue
            plan=load(p)
            for name in plan.get('dependencies',[]): safe(self.root,name)
            for row in plan['requests']:
                safe(self.root,row['directory'])
                for name in row.get('inputs',[]): safe(self.root,name)
        state = trusted.module('workflow',self.method).final_state(self.root)
        self.current_state = state
        by_doc = {}
        for d in state['documents']:
            for e in d['logical']['elements']:
                self._bind_fragment_files(e)
            by_doc[d['identity']] = d
        for doc in self.manifest['documents']:
            identity = doc['identity']
            d = by_doc[identity]
            require(sha(self.root / doc['raw']) == doc['sha256'], 'source-hash-mismatch:' + identity)
            self._candidates[identity] = d['candidates']
            self.documents.append(dict(identity=identity, raw=doc['raw'], sha256=doc['sha256'],
                                       page_count=doc['page_count'], channels=list(doc.get('channels', [])),
                                       extraction_scope=doc.get('extraction_scope'), elements=d['logical']['elements'],
                                       pages={p['page']: p for p in doc['pages']},
                                       schema='pdf-source-package-v1', source_complete=d['complete_package'],
                                       source_status='complete' if d['complete_package'] else 'source-incomplete',
                                       gaps=d['gaps'], logical_dispositions={k:v for k,v in d['logical'].items() if k!='elements'},
                                       candidate_count=len(d['candidates']), source_fixture=state['fixture']))

    # ---------- historical schema (explicit, small adapter) ----------

    def _load_historical(self):
        # Historical documents carry: identity, directory, raw_pdf, pages (int).
        # No channels field; never fed to current final_state.
        for doc in self.manifest['documents']:
            identity = doc['identity']
            directory = safe(self.root, doc['directory'])
            require(directory.is_dir(), 'historical-doc-directory')
            raw = doc['raw_pdf']
            require(safe(self.root, raw).is_file(), 'historical-raw-pdf')
            logical = load(directory / 'logical-elements.json')
            elements = logical['elements']
            for e in elements:
                self._bind_fragment_files(e)
            components = load(directory / 'components.json') if (directory / 'components.json').is_file() else []
            self._candidates[identity] = components
            self.documents.append(dict(identity=identity, raw=raw, sha256=sha(self.root / raw),
                                       page_count=doc['pages'], channels=['caption', 'figure', 'structured'],
                                       extraction_scope='whole-document', elements=elements,
                                       pages={}, schema='offline-saved-response-document-update-v1 (historical adapter)',
                                       source_complete=False, source_status='historical-pilot-only',
                                       gaps=[{'status':'historical-not-current-production-validation'}],
                                       logical_dispositions={k:v for k,v in logical.items() if k!='elements'},
                                       candidate_count=len(components), source_fixture=False))

    def _bind_fragment_files(self, element):
        """Verify fragment crops exist and match recorded hashes; keep read-only refs."""
        for f in element['ordered_source_fragments']:
            crop = f.get('crop')
            if crop is not None:
                p = safe(self.root, crop)
                require(p.is_file(), 'missing-fragment-crop:' + crop)
                require(f.get('crop_sha256') is None or sha(p) == f['crop_sha256'],
                        'fragment-crop-hash:' + crop)
        require(element.get('source_document'), 'element-source-document')

    # ---------- accessors ----------

    def candidates(self, identity):
        require(identity in self._candidates, 'unknown-document:' + identity)
        return self._candidates[identity]

    def candidate(self, identity, candidate_id):
        for c in self.candidates(identity):
            if c['id'] == candidate_id:
                return c
        raise ValueError('unknown-candidate:' + candidate_id)

    def doc(self, identity):
        for d in self.documents:
            if d['identity'] == identity:
                return d
        raise ValueError('unknown-document:' + identity)

    def native_lines(self, identity, page):
        """All native lines of a physical page, keyed by line ID (current schema only)."""
        d = self.doc(identity)
        pinfo = d['pages'].get(page)
        require(pinfo is not None, 'page-unknown:' + str(page))
        nt = pinfo.get('native_text')
        require(nt, 'historical-package-no-page-native-text')
        return {l['id']: l for l in load(self.root / nt)}

    # ---------- element selection ----------

    def eligible_elements(self, kinds):
        """Elements with explicit per-element eligibility rows (exact accounting input)."""
        rows = []
        for doc in self.documents:
            for e in doc['elements']:
                ct = e['content_type']
                kind = {'figure': 'figure', 'table': 'table', 'algorithm': 'algorithm',
                        'code': 'algorithm', 'data-file': 'table'}.get(ct)
                pages = [f['page'] for f in e['ordered_source_fragments']]
                refs = e['body_refs'] + e['caption_note_refs']
                base = dict(element_id=e['id'], document=doc['identity'], content_type=ct,
                           label=e.get('label'), pages=pages, candidate_refs=refs)
                if kind is None or kind not in kinds:
                    rows.append(dict(base, kind=None, reason='unknown-type' if kind is None else 'not-selected', element=e))
                elif e.get('status') not in (None, 'reference-validated; semantic review pending',
                                             'deterministically assembled; semantic review pending-parent',
                                             'deterministically updated; semantic review pending-parent'):
                    # None covers adapters whose saved elements carry no status field.
                    rows.append(dict(base, kind=None, reason='element-not-reference-validated', element=e))
                else:
                    rows.append(dict(base, kind=kind, reason='eligible', element=e))
        return rows
