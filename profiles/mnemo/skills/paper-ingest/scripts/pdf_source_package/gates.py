"""Full local counts, immutable phase approvals, one-attempt reservations."""
from dataclasses import dataclass
from pathlib import Path
import copy
import fcntl
import os
import time
from .io import *
from . import preparation, grouping
from .counting import Counter, processor, REVISION, MODEL_REPO

PHASES = ('initial', 'classification', 'association')


def count_phase(root, phase, cache):
    root = Path(root); require(phase in PHASES, 'phase')
    require(not (root / f'{phase}-seal.json').exists(), 'phase-already-sealed')
    plan = load(root / f'{phase}-plan.json')
    require(all(r['status'] == 'uncounted' for r in plan['requests']), 'count-is-one-shot')
    assets = Path(cache) / ('models--' + MODEL_REPO.replace('/', '--')) / 'snapshots' / REVISION
    require(assets.is_dir(), 'official-processor-revision-not-cached')
    asset_hashes = {p.name: sha(p) for p in sorted(assets.iterdir()) if p.is_file()}
    require(asset_hashes, 'empty-processor-assets')
    counter = Counter(processor(cache))
    for row in plan['requests']:
        p = root / row['directory']; wire = load(p / 'request-wire.json')
        require({k:v for k,v in wire.items() if k != 'messages'} == SETTINGS, 'request-settings')
        counted = counter.count(wire)
        if not counted['fits'] and row['channel'] in ('figure','structured'):
            put(p / 'compact-flat-wire.json', (p / 'request-wire.json').read_bytes())
            save(p / 'compact-flat-count.json', dict(counted, request_sha256=sha(p / 'request-wire.json')))
            put(p / 'compact-flat-mapping.json', (p / 'mapping.json').read_bytes())
            put(p / 'compact-flat-inventory.json', (p / 'encoded-inventory.json').read_bytes())
            inv = load(root / row['page_directory'] / 'inventory.json')
            mapping, evidence = grouping.partition(root / row['raw'], inv)
            save(p / 'grouping-evidence.json', evidence)
            require(evidence['summary']['native_mapping_verified'], 'native-grouping-identity-blocked')
            parts = wire['messages'][0]['content'][1:]
            wire, mapping, encoded = preparation.body_request(inv, parts, row['channel'], mapping)
            save(p / 'request-wire.json', wire, replace=True)
            save(p / 'mapping.json', mapping, replace=True)
            save(p / 'encoded-inventory.json', encoded, replace=True)
            row['inputs'] += [row['directory'] + '/' + n for n in ('compact-flat-wire.json','compact-flat-count.json',
                'compact-flat-mapping.json','compact-flat-inventory.json','grouping-evidence.json')]
            counted = counter.count(wire); row['representation'] = 'native-clip-units-after-measured-overflow'
        elif not counted['fits'] and row['channel'] == 'association':
            put(p / 'whole-document-wire.json', (p / 'request-wire.json').read_bytes())
            save(p / 'whole-document-count.json', dict(counted, request_sha256=sha(p / 'request-wire.json')))
            doc = next(d for d in load(root / 'manifest.json')['documents'] if d['identity'] == row['document'])
            cs = load(p / 'candidates.json'); selected = {c['page'] for c in cs}
            pages = [p for p in doc['pages'] if p['page'] in selected and p['policy']['disposition'] == 'eligible']
            wire = preparation.association_request(root, doc, cs, pages, True)
            save(p / 'request-wire.json', wire, replace=True)
            row['inputs'] += [row['directory'] + '/' + n for n in ('whole-document-wire.json','whole-document-count.json')]
            counted = counter.count(wire); row['representation'] = 'candidate-page-images-full-native'
            row['image_omitted_pages'] = [p['page'] for p in doc['pages'] if p['page'] not in selected]
        row['request_sha256'] = sha(p / 'request-wire.json')
        counted['request_sha256'] = row['request_sha256']
        row['count'] = counted; row['status'] = 'ready' if counted['fits'] else 'preflight-context-overflow'
        save(p / 'count.json', counted)
        print(__import__('json').dumps(dict(phase='counted', id=row['id'], tokens=counted['prompt_tokens_local'], fits=counted['fits'])), flush=True)
    plan['processor'] = dict(cache=str(Path(cache).absolute()), revision=REVISION, files=asset_hashes)
    save(root / f'{phase}-plan.json', plan, replace=True)
    return plan


def seal(root, phase):
    root = Path(root); plan = load(root / f'{phase}-plan.json')
    require(phase in PHASES and all(r['status'] in ('ready','preflight-context-overflow') for r in plan['requests']), 'count-before-seal')
    manifest = load(root / 'manifest.json')
    names = set(plan['dependencies']) | {'manifest.json', f'{phase}-plan.json'}
    for row in plan['requests']:
        names.update(row['inputs']); names.update(row['directory'] + '/' + n for n in ('request-wire.json','count.json'))
    names.update(d['raw'] for d in manifest['documents'])
    freeze = dict(schema='pdf-phase-seal-v1', phase=phase, code=code_hashes(),
                  files={n: sha(safe(root, n)) for n in sorted(names)})
    save(root / f'{phase}-seal.json', freeze)
    approval = expected(root, phase)
    save(root / f'{phase}-approval.template.json', approval)
    return approval


def expected(root, phase):
    root = Path(root); manifest = load(root / 'manifest.json'); plan = load(root / f'{phase}-plan.json')
    return dict(schema='pdf-parent-approval-v1', phase=phase, approved=False, approved_by=None,
        source_and_candidates_reviewed=False, payload_counts_reviewed=False, current_route_reviewed=False,
        seal_sha256=sha(root / f'{phase}-seal.json'), code=code_hashes(), endpoint=manifest['endpoint'],
        settings=SETTINGS, timeout_seconds=TIMEOUT, retries=0, reasoning='omitted/default',
        requests=[dict(id=r['id'], request_sha256=r['request_sha256'], count=r['count']) for r in plan['requests'] if r['status']=='ready'],
        maximum_phase_posts=sum(r['status']=='ready' for r in plan['requests']), maximum_total_posts=manifest['maximum_posts'])


def stamp(p):
    s = Path(p).stat()
    return (s.st_dev, s.st_ino, s.st_size, s.st_mtime_ns, s.st_ctime_ns)


@dataclass(frozen=True)
class EntrySnapshot:
    root: Path
    phase: str
    approval_path: Path
    approval_bytes: bytes
    seal_bytes: bytes
    plan_bytes: bytes
    code_bytes: bytes
    shared_stamps: tuple

    @classmethod
    def capture(cls, root, phase, approval):
        root = Path(root).absolute(); approval = Path(approval).absolute()
        require(phase in PHASES, 'phase')
        approval_bytes = approval.read_bytes()
        seal_bytes = (root / f'{phase}-seal.json').read_bytes()
        plan_bytes = (root / f'{phase}-plan.json').read_bytes()
        a = strict(approval_bytes); want = expected(root, phase)
        flags = {'approved','approved_by','source_and_candidates_reviewed','payload_counts_reviewed','current_route_reviewed'}
        require(set(a) == set(want), 'approval-schema')
        require(isinstance(a['approved_by'],str) and a['approved_by'].strip() and
                all(a[k] is True for k in flags - {'approved_by'}), 'explicit-parent-approval-required')
        require(all(a[k] == want[k] for k in set(want) - flags), 'approval-bindings-changed')
        frozen = load(root / f'{phase}-seal.json')
        require(frozen['code'] == code_hashes(), 'code-changed')
        stamps = []
        for name, h in frozen['files'].items():
            p = safe(root, name); before = stamp(p)
            require(sha(p) == h and stamp(p) == before, 'sealed-input-changed:' + name)
            stamps.append((name, before))
        plan = load(root / f'{phase}-plan.json')
        if plan['requests']:
            assets = Path(plan['processor']['cache']) / ('models--' + MODEL_REPO.replace('/', '--')) / 'snapshots' / REVISION
            require({p.name: sha(p) for p in sorted(assets.iterdir()) if p.is_file()} == plan['processor']['files'], 'processor-assets-changed')
        result = cls(root, phase, approval, approval_bytes, seal_bytes,
                     plan_bytes, dumps(code_hashes()), tuple(stamps))
        result.check()
        return result

    @property
    def rows(self):
        return [r for r in strict(self.plan_bytes)['requests'] if r['status'] == 'ready']

    def check(self, row=None, payload=None):
        require(not (self.root / 'stop.json').exists(), 'shared-stop-pending')
        require(self.approval_path.read_bytes() == self.approval_bytes, 'entry-approval-changed')
        require((self.root / f'{self.phase}-seal.json').read_bytes() == self.seal_bytes, 'entry-seal-changed')
        require((self.root / f'{self.phase}-plan.json').read_bytes() == self.plan_bytes, 'entry-plan-changed')
        require(dumps(code_hashes()) == self.code_bytes, 'entry-code-changed')
        # Full shared content was hashed once at phase entry. Metadata changes
        # reject even coordinated edits; current request content is hashed again.
        for name, previous in self.shared_stamps:
            require(stamp(safe(self.root,name)) == previous, 'entry-input-changed:' + name)
        if row is not None:
            require(row in self.rows, 'unapproved-request')
            frozen = strict(self.seal_bytes)['files']
            for name in set(row['inputs']) | {row['directory'] + '/request-wire.json', row['directory'] + '/count.json'}:
                require(sha(safe(self.root, name)) == frozen[name], 'current-request-input-changed:' + name)
            raw = (self.root / row['directory'] / 'request-wire.json').read_bytes()
            require(digest(raw) == row['request_sha256'] and (payload is None or payload == raw), 'wire-changed')
            n = row['count']['prompt_tokens_local']
            require(type(n) is int and n > 0 and n + SETTINGS['max_tokens'] <= LIMIT and row['count']['fits'] is True, 'count-invalid')


def reserve(entry, row, origin):
    entry.check(row)
    root = entry.root
    # Serialize budget check and durable exclusive reservation across processes.
    with (root / 'reservation.lock').open('a+b') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        require(not (root / row['directory'] / 'reservation.json').exists(), 'consumed-reservation')
        count = sum(1 for _ in (root / 'requests').glob('*/reservation.json'))
        require(count < strict(entry.approval_bytes)['maximum_total_posts'], 'request-budget-consumed')
        return save(root / row['directory'] / 'reservation.json', dict(phase=entry.phase,
            request_sha256=row['request_sha256'], approval_sha256=digest(entry.approval_bytes),
            seal_sha256=digest(entry.seal_bytes), transport_origin=origin, pid=os.getpid(),
            epoch=time.time(), state='reserved-may-have-posted'))
