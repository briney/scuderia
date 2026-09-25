"""Exact element accounting for the enrichment stage.

Every eligible logical element ends with an enrichment output OR an explicit
disposition: failed / partial / unsupported / pending / not-selected /
unknown-type / source-incomplete. Mechanical schema validity is separate
from scientific accuracy and from human acceptance.
"""
from .io import require

DISPOSITIONS = ('enriched', 'failed', 'partial', 'unsupported', 'pending', 'not-selected', 'unknown-type',
                'source-incomplete', 'prepared-not-sent', 'interrupted')


def accounting(plan, results):
    """plan: enrichment-plan manifest rows; results: {request_id: outcome dict}.

    Returns an accounting record covering every element in the source
    package's selection scope, not only those with requests.
    """
    require(isinstance(plan, dict) and isinstance(plan.get('requests'), list), 'plan-shape')
    require(isinstance(results, dict), 'results-shape')
    rows = []
    seen = set()
    request_ids=[r['id'] for r in plan['requests'] if r.get('id')]
    require(len(request_ids)==len(set(request_ids)), 'duplicate-request-id')
    require(set(results) <= set(request_ids), 'unknown-result-id')
    for row in plan['requests']:
        eid = row['element_id']
        require(eid not in seen, 'duplicate-element-id')
        seen.add(eid)
        if row.get('kind') is None:
            rows.append(dict(element_id=eid, document=row['document'], kind=None,
                             status={'kind-not-selected':'not-selected','element-not-reference-validated':'source-incomplete'}.get(row.get('status'),row.get('status','not-selected')), request_ids=[],
                             not_proof_of_absence=True, reason='kind-not-selected-or-element-skipped'))
            continue
        outcome = results.get(row.get('id'))
        if outcome is None:
            rows.append(dict(element_id=eid, document=row['document'], kind=row['kind'],
                             status='prepared-not-sent', request_ids=[row['id']],
                             not_proof_of_absence=True,
                             reason='Request prepared but no response imported yet.'))
            continue
        status = outcome.get('status', 'failed')
        rows.append(dict(element_id=eid, document=row['document'], kind=row['kind'],
                         status=status, request_ids=[row['id']],
                         complete=outcome.get('complete', False),
                         not_proof_of_absence=status not in ('enriched',),
                         reason=outcome.get('reason')))
    source_rows={r['element_id']:r for r in plan['requests']}
    for entry in rows:
        source=source_rows[entry['element_id']]
        entry['variant']='caption-only' if source.get('caption_only') else 'image-plus-caption'
        entry['scientific_review']='pending'
        entry['coverage']=results.get(source.get('id'),{}).get('record',{}).get('coverage')
    require(all(r['status'] in DISPOSITIONS for r in rows), 'unknown-disposition')
    documents=[]
    for doc in plan.get('documents',[]):
        elements=[r for r in rows if r['document']==doc['identity']]
        documents.append(dict(doc, element_count=len(elements), selected_count=sum(r['kind'] is not None for r in elements)))
    require(len({d['identity'] for d in documents})==len(documents), 'duplicate-document-id')
    return dict(schema='enrichment-accounting-v3', elements=rows, documents=documents,
                counts={d: sum(1 for r in rows if r['status'] == d) for d in DISPOSITIONS},
                total_elements_accounted=len(rows),
                all_accounted=True,
                note='Exact accounting: every element in the prepared selection scope has an output or an '
                     'explicit disposition. Mechanical schema validity != scientific accuracy != human acceptance.')


def gaps(account):
    """Visible-gap projection for reporting."""
    out = []
    for r in account['elements']:
        if r['status'] == 'enriched' and r.get('complete'):
            continue
        out.append(dict(element_id=r['element_id'], status=r['status'], reason=r.get('reason')))
    return out
