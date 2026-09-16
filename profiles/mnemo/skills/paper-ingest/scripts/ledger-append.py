#!/usr/bin/env python3
"""Single-writer ledger append for people/_ledger.yaml (paper-ingest Phase 8, Branch 3).

Usage: edit PAPER/NEW_BLOCKS below, `write_file` this script to /tmp/, then run
`python3 /tmp/ledger-append.py` from the brain root — heredocs and multi-line
`python3 -c` are blocked by tirith, so the script file is the executable form.

Concurrency: parallel paper-ingest workers append to the same ledger, so the
whole read → dedup → candidate-build → validate → publish → verify sequence
runs under one deterministic lock — a hash of the *resolved* ledger path in
tempfile.gettempdir(), held with fcntl.flock. POSIX only (the mnemo workflow
is); fcntl is not importable on Windows.

Publication is atomic: the full candidate file is built and validated as text
before the live ledger is ever touched, then written to a temporary sibling
regular file, flushed + fsync'd, its mode copied from the ledger, and
os.replace'd over the ledger (fsync of the parent directory where supported).
A crash or validation failure never truncates the live ledger, and temp files
are cleaned up on failure.

The append is PLAIN-TEXT of pre-rendered blocks — never `yaml.safe_dump`
the re-loaded file (a safe_dump round-trip re-flows every long line and
re-orders keys: a 9-entry append becomes a 10k-line whole-file rewrite).
`yaml.safe_load` is used read-only, for the pre-append dedup check and the
post-append verification.

For tests, call `append_blocks(ledger, paper, blocks)` directly — no class,
no framework, no retry loop.
"""
import fcntl
import hashlib
import os
import sys
import tempfile

import yaml

LEDGER = 'people/_ledger.yaml'   # run from the brain root

# ---- EDIT THESE -----------------------------------------------------------
PAPER = 'papers/<this-paper-slug>'

NEW_BLOCKS = [
    # Block shape: name / slug / orcid / affiliations / citations.
    # orcid: null unless verified from PubMed XML, EPMC, or Crossref —
    # never fabricate. Days-old arXiv preprints have no Crossref deposit
    # yet; null is correct there.
    """\
- name: <Display Name>
  slug: <slug>
  orcid: null
  affiliations:
    - <Affiliation>
  citations:
    - papers/<this-paper-slug>
""",
    # ... one block per new author
]
# ---------------------------------------------------------------------------

def _lock_path(ledger: str) -> str:
    resolved = os.path.realpath(ledger)
    digest = hashlib.sha256(resolved.encode('utf-8')).hexdigest()
    return os.path.join(tempfile.gettempdir(), f'ledger-append-{digest}.lock')


def _candidate_text(current: str, blocks) -> str:
    if current and not current.endswith('\n'):
        current += '\n'
    return current + ''.join(blocks)


def _validate(text: str, slugs, paper: str) -> None:
    data = yaml.safe_load(text)
    entries = data['entries'] if isinstance(data, dict) else data
    if not entries:
        sys.exit('ABORT - candidate text does not parse into ledger entries')
    all_slugs = [e['slug'] for e in entries if isinstance(e, dict) and 'slug' in e]
    dupes = {s for s in all_slugs if all_slugs.count(s) > 1}
    assert not dupes, f'duplicate slugs: {dupes}'
    for slug in slugs:
        match = [e for e in entries if e.get('slug') == slug]
        assert match and paper in (match[0].get('citations') or []), \
            f'{slug} missing or citation lost'


def append_blocks(ledger: str, paper: str, blocks) -> None:
    """Append plain-text blocks to `ledger` under a deterministic flock.

    Safe among local concurrent invocations for the same ledger. A second
    invocation for the same slug acquires the lock after the first, rereads
    the new ledger, fails the dedup check, and aborts without changing it.
    """
    lock_path = _lock_path(ledger)
    lock_fd = os.open(lock_path, os.O_CREAT | os.O_RDWR, 0o600)
    try:
        fcntl.flock(lock_fd, fcntl.LOCK_EX)

        # Read + dedup under the lock — never before.
        with open(ledger) as f:
            data = yaml.safe_load(f)
        existing = {e['slug'] for e in data['entries']}
        incoming = []
        for block in blocks:
            slug = next(l.split(':', 1)[1].strip()
                        for l in block.splitlines()
                        if l.strip().startswith('slug:'))
            incoming.append(slug)
        overlap = existing & set(incoming)
        if overlap:
            sys.exit(f'ABORT - slugs already exist: {overlap}')

        # Build and validate the full candidate text before touching the ledger.
        with open(ledger) as f:
            current = f.read()
        candidate = _candidate_text(current, blocks)
        _validate(candidate, incoming, paper)

        # Atomic publish: temp sibling regular file → fsync → os.replace.
        ledger_dir = os.path.dirname(os.path.abspath(ledger))
        mode = os.stat(ledger).st_mode & 0o7777
        fd, tmp_path = tempfile.mkstemp(
            dir=ledger_dir, prefix='._ledger-append-', suffix='.yaml')
        tmp_path = os.path.realpath(tmp_path)
        try:
            with os.fdopen(fd, 'w') as f:
                f.write(candidate)
                f.flush()
                os.fsync(f.fileno())
            os.chmod(tmp_path, mode)
            os.replace(tmp_path, ledger)
            tmp_path = None  # published; nothing left to clean
        finally:
            if tmp_path is not None and os.path.exists(tmp_path):
                os.unlink(tmp_path)
        parent_fd = os.open(ledger_dir, os.O_RDONLY)
        try:
            os.fsync(parent_fd)
        except OSError:
            pass  # directory fsync unsupported (some filesystems)
        finally:
            os.close(parent_fd)

        # Read-back verification.
        with open(ledger) as f:
            check = yaml.safe_load(f)
        slugs = [e['slug'] for e in check['entries']]
        print(f'appended {len(incoming)} entries; total {len(slugs)}; '
              f'no dupes; all citations verified')
    finally:
        os.close(lock_fd)  # releases the flock


def main():
    append_blocks(LEDGER, PAPER, NEW_BLOCKS)


if __name__ == '__main__':
    main()
