#!/usr/bin/env python3
"""Retrieve one public metadata/document URL into a new external evidence directory.

No parsing, inference, automatic retries, authentication, or execution of fetched
content. A successful download is a candidate, not article identity verification.
"""
import argparse
import hashlib
import http.client
import json
from pathlib import Path
import urllib.request
import time
import signal

from fetch_fulltext import AcquisitionEvidence, UA
from article_archive_compat.portable_articles import put
from article_archive_compat.source_package import identifier, public_url


def reserve_attachment(state,attachment,url):
    from manuscript_ingest import workflow as w
    state=w.outside_instance(state); identifier(attachment); public_url(url)
    with w.locked(state.parent):
        value=json.loads(state.read_text()) if state.exists() else dict(started_at=time.time(),attempts={})
        attempts=value['attempts'].setdefault(attachment,[])
        w.require(len(attempts)<2 and url not in attempts,'attachment-attempt-limit; record deferred')
        remaining=120-(time.time()-value['started_at'])
        w.require(remaining>0,'supplement-budget-exhausted; record deferred')
        attempts.append(url); w.save(state,value)
        return remaining


def budget_expired(signum,frame):
    raise TimeoutError('supplement-budget-exhausted')


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--url', required=True, help='Observed public HTTP(S) source URL')
    parser.add_argument('--evidence-dir', required=True, type=Path,
                        help='New or empty absolute directory outside the brain; parent must exist')
    parser.add_argument('--filename', required=True,
                        help='Safe basename with the source extension, e.g. details.json or manuscript.pdf')
    parser.add_argument('--supplement-state',type=Path,help='Shared external per-paper 120-second attachment budget file')
    parser.add_argument('--attachment',help='Stable attachment identifier; requires --supplement-state')
    args = parser.parse_args(argv)
    previous=None
    try:
        if bool(args.supplement_state)!=bool(args.attachment):raise ValueError('attachment-budget-arguments-required')
        if args.supplement_state:
            remaining=reserve_attachment(args.supplement_state,args.attachment,args.url)
            previous=signal.signal(signal.SIGALRM,budget_expired)
            signal.setitimer(signal.ITIMER_REAL,remaining)
        public_url(args.url)
        identifier(args.filename)
        evidence = AcquisitionEvidence(args.evidence_dir)
        with evidence.open(urllib.request.Request(args.url, headers={'User-Agent': UA})) as response:
            raw = response.read()
            status = response.code
            final_url = response.geturl()
            content_type=response.headers.get('Content-Type')
        if not raw:
            raise ValueError('empty response')
        path = evidence.root / 'derived' / args.filename
        put(path, raw)
        print(json.dumps(dict(file=str(path), bytes=len(raw), sha256=hashlib.sha256(raw).hexdigest(),
                              status=status, source_url=args.url, final_url=final_url,
                              content_type=content_type,evidence_dir=str(evidence.root), identity_verified=False,**evidence.source_inventory())))
        return 0
    except (OSError, ValueError, RuntimeError, http.client.HTTPException) as exc:
        # Server errors can reflect credentials; raw HTTP evidence stays external.
        print(json.dumps(dict(error=type(exc).__name__, status=getattr(exc, 'code', None),
                              message='Retrieval failed. Inspect external evidence if created; do not treat this as a source.')))
        return 2
    finally:
        if previous is not None:
            signal.setitimer(signal.ITIMER_REAL,0)
            signal.signal(signal.SIGALRM,previous)


if __name__ == '__main__':
    raise SystemExit(main())
