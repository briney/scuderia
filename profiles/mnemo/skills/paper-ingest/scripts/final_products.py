"""Retired execution entry point. Historical readers live outside the skill tree."""
import json

def refuse(*args, **kwargs):
    return dict(status='held',blocking_reason='retired-workflow',next_action='Use paper_ingest.')

def main(argv=None):
    print(json.dumps(refuse())); return 2

launch = execute = advance = operator = route = refuse

from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[3]/'tools'))
from article_archive_compat.final_products import verify, verify_ingest, verify_publication
from article_archive_compat.article_runtime import absolute

if __name__=='__main__':raise SystemExit(main())
