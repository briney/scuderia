"""Shared fixture/environment setup for the existing unittest entry points."""
import hashlib
import json
import os
from pathlib import Path
import sys
import tarfile
import tempfile

ROOT = Path(__file__).resolve().parent
_PROTECTIONS = []


def release_protection():
    """Allow the owning runner to remove its disposable inputs after the suite."""
    for roots in _PROTECTIONS:
        roots.clear()


def install_guard():
    protected = [ROOT/'test-fixtures'] + [Path(p).resolve() for p in os.environ.get('PDF_TEST_PROTECTED', '').split(os.pathsep) if p]
    if os.environ.get('PAPER_INGEST_FIXTURE_BUNDLE'):
        protected.append(Path(os.environ['PAPER_INGEST_FIXTURE_BUNDLE']).resolve())
    _PROTECTIONS.append(protected)
    forbidden = [ROOT/'runs'] + [Path(p).resolve() for p in os.environ.get('PDF_TEST_FORBIDDEN', '').split(os.pathsep) if p]
    def audit(event, args):
        if event.startswith('socket.'):
            raise RuntimeError('offline-network-blocked')
        if event not in ('open', 'os.listdir', 'os.scandir', 'os.remove', 'os.rename', 'os.rmdir', 'os.mkdir'):
            return
        paths = args[:2] if event == 'os.rename' else args[:1]
        write = event in ('os.remove', 'os.rename', 'os.rmdir', 'os.mkdir')
        if event == 'open':
            write = bool(args[2] & (os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC | os.O_APPEND))
        for value in paths:
            if not isinstance(value, (str, bytes)):
                continue
            path = Path(os.fsdecode(value)).resolve()
            if any(path.is_relative_to(root) for root in forbidden):
                raise RuntimeError('historical-input-forbidden:' + str(path))
            if write and any(path.is_relative_to(root) for root in protected):
                raise RuntimeError('protected-test-input:' + str(path))
    sys.addaudithook(audit)


def configure(scratch, *, adapter=None, processor_cache=None, fixtures=None):
    scratch = Path(scratch).resolve()
    scratch.mkdir(parents=True, exist_ok=True)
    fixtures = Path(fixtures).resolve() if fixtures else scratch/'inputs'
    if not fixtures.exists():
        bundle = Path(os.environ.get('PAPER_INGEST_FIXTURE_BUNDLE', ROOT/'test-fixtures')).resolve()
        manifest = json.loads((bundle/'manifest.json').read_text())
        fixtures.mkdir()
        for name,record in manifest.items():
            archive=bundle/name
            if hashlib.sha256(archive.read_bytes()).hexdigest() != record['sha256']:
                raise ValueError('fixture-archive-hash-mismatch:'+name)
            with tarfile.open(archive, mode='r:xz') as stream:
                stream.extractall(fixtures, filter='data')
    for key in list(os.environ):
        if key.endswith(('_API_KEY', '_TOKEN', '_PASSWORD', '_SECRET')):
            del os.environ[key]
    paths = [ROOT, ROOT.parent, ROOT.parent, ROOT.parent,
             ROOT/'qualified_enrichment', ROOT/'pdf_enrichment']
    if adapter:
        adapter = Path(adapter).resolve(); paths.insert(0, adapter)
    os.environ.update(PYTHONDONTWRITEBYTECODE='1', PDF_SOURCE_PACKAGE_OFFLINE='1', PDF_ENRICHMENT_OFFLINE='1',
        HF_HUB_OFFLINE='1', TRANSFORMERS_OFFLINE='1', TMPDIR=str(scratch),
        PDF_ENRICHMENT_METHOD=str(ROOT.parent), REENRICH_ENRICHMENT_ROOT=str(ROOT.parent),
        REENRICH_INTEGRATION_ROOT=str(ROOT.parent),
        PDF_TEST_FIXTURES=str(fixtures/'method'), PDF_ENRICHMENT_FIXTURES=str(fixtures),
        PDF_TEST_WORK=str(scratch/'method-work'), PDF_ENRICHMENT_TEST_SCRATCH=str(scratch/'enrichment-work'),
        UNCERTAINTY_SCRATCH=str(scratch/'integration-work'), SOURCE_PACKAGE_TEST_ROOT=str(scratch),
        PORTABLE_ARTICLES_DONOR=str(fixtures/'current'))
    for name in ('method-work', 'enrichment-work', 'integration-work'):
        (scratch/name).mkdir(exist_ok=True)
    if adapter:
        os.environ['UNCERTAINTY_ADAPTER'] = str(adapter)
    os.environ['PDF_TEST_PROCESSOR'] = '1' if processor_cache else '0'
    cache = Path(processor_cache).resolve() if processor_cache else scratch/'synthetic-processor'
    sys.path[:0] = list(map(str, paths))
    if not processor_cache:
        from pdf_source_package.counting import MODEL_REPO, REVISION
        assets = cache/('models--'+MODEL_REPO.replace('/', '--'))/'snapshots'/REVISION
        assets.mkdir(parents=True, exist_ok=True)
        (assets/'OFFLINE-FIXTURE.txt').write_text('Synthetic asset binding only; not a tokenizer or measured count.\n')
    os.environ.update(PDF_PROCESSOR_CACHE=str(cache), REENRICH_PROCESSOR_CACHE=str(cache))
    # Python children install exactly the same offline/protected-input guard.
    guard = scratch/'python-guard'; guard.mkdir(exist_ok=True)
    (guard/'sitecustomize.py').write_text('from offline_test_support import install_guard\ninstall_guard()\n')
    paths.insert(0, guard)
    sys.path[:0] = list(map(str, paths))
    os.environ['PYTHONPATH'] = os.pathsep.join(map(str, paths))
    os.environ['PDF_TEST_PROTECTED'] = str(fixtures)
    os.environ.setdefault('PDF_TEST_FORBIDDEN', str(ROOT/'runs'))
    sys.dont_write_bytecode = True
    tempfile.tempdir = str(scratch)
    install_guard()
    return fixtures

# Reject historical/bundle writes even during runner setup, before configure().
install_guard()
