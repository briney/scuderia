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

from fetch_fulltext import AcquisitionEvidence, UA
from article_archive_compat.portable_articles import put
from article_archive_compat.source_package import identifier, public_url


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--url', required=True, help='Observed public HTTP(S) source URL')
    parser.add_argument('--evidence-dir', required=True, type=Path,
                        help='New absolute directory outside the brain; parent must exist')
    parser.add_argument('--filename', required=True,
                        help='Safe basename with the source extension, e.g. details.json or manuscript.pdf')
    args = parser.parse_args(argv)
    try:
        public_url(args.url)
        identifier(args.filename)
        evidence = AcquisitionEvidence(args.evidence_dir)
        with evidence.open(urllib.request.Request(args.url, headers={'User-Agent': UA})) as response:
            raw = response.read()
            status = response.code
            final_url = response.geturl()
        if not raw:
            raise ValueError('empty response')
        path = evidence.root / 'derived' / args.filename
        put(path, raw)
        print(json.dumps(dict(file=str(path), bytes=len(raw), sha256=hashlib.sha256(raw).hexdigest(),
                              status=status, source_url=args.url, final_url=final_url,
                              evidence_dir=str(evidence.root), identity_verified=False)))
        return 0
    except (OSError, ValueError, RuntimeError, http.client.HTTPException) as exc:
        # Server errors can reflect credentials; raw HTTP evidence stays external.
        print(json.dumps(dict(error=type(exc).__name__, status=getattr(exc, 'code', None),
                              message='Retrieval failed. Inspect external evidence if created; do not treat this as a source.')))
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
