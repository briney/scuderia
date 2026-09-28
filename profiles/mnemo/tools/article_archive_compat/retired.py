"""Explicit refusal for obsolete executors; no legacy enable switch."""
def refuse(*args, **kwargs):
    return dict(status='held', blocking_reason='retired-workflow', next_action='Use paper_ingest for manuscript-to-page ingestion.')

def main(argv=None):
    import json
    print(json.dumps(refuse()))
    return 2
