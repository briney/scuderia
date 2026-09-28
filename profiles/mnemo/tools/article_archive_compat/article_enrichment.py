"""Historical read-only dependency closure; extracted without changing validation contracts."""
from __future__ import annotations
from article_archive_compat.article_runtime import require

def validate_accounting(accounting):
    statuses = ('pending', 'uncertain', 'failed', 'completed')
    rows = accounting['requests']
    require(all((row['status'] in statuses for row in rows.values())), 'unknown-request-status')
    counts = {status: sum((row['status'] == status for row in rows.values())) for status in statuses}
    require(accounting['counts'] == counts and accounting['complete'] is (counts['completed'] == len(rows)) and (accounting['integrity_hold'] is any((row.get('failure', {}).get('fatal', False) for row in rows.values()))), 'request-accounting-binding')

def readiness(accounting, assessment, source=None):
    pending = {rid for (rid, row) in accounting['requests'].items() if row['status'] == 'pending'}
    if source is not None:
        from article_archive_compat.source_package import validate_source_readiness
        validate_source_readiness(source)
        pending.update(source['pending'])
    accounted = not pending or bool(assessment is not None and set(assessment['unattempted']) == pending)
    holds = [h for h in source['holds'] if not h.startswith('fixture-')] if source is not None else []
    if not accounted:
        holds.append('unaccounted-pending-requests')
    if accounting['integrity_hold']:
        holds.append('execution-integrity-hold')
    if assessment is None or not assessment['usable_evidence']:
        holds.append('usable-evidence-review-required')
    return dict(requests_accounted_for=accounted, requests_successful=accounting['complete'], page_ready=not holds, holds=holds)
