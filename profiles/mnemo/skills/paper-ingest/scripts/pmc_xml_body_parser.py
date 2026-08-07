#!/usr/bin/env python3
"""pmc_xml_body_parser.py — extract structured body text from a PMC JATS XML file.

Referenced by paper-ingest-pubmed-resolver-v2 §4. Reuses the parser in
fetch_fulltext.py (same directory).

Usage:
  python3 pmc_xml_body_parser.py /tmp/paper.xml                 # first 15k chars
  python3 pmc_xml_body_parser.py /tmp/paper.xml --range 15000 30000
  python3 pmc_xml_body_parser.py /tmp/paper.xml --full
"""

import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from fetch_fulltext import pmc_xml_to_text  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("xml_file")
    ap.add_argument("--range", nargs=2, type=int, metavar=("START", "END"))
    ap.add_argument("--full", action="store_true")
    args = ap.parse_args()

    with open(args.xml_file) as f:
        text = pmc_xml_to_text(f.read())

    if not text:
        print("(no <body> found — metadata-only XML or parse failure)")
        return

    if args.full:
        print(text)
    elif args.range:
        print(text[args.range[0]:args.range[1]])
    else:
        print(text[:15000])

    print("\n---\n[total chars: %d]" % len(text), file=sys.stderr)


if __name__ == "__main__":
    main()
