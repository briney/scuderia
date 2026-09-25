import re, copy
from . import native as pilot
from .io import require

def observed_label(label, native_text):
    # Preserve observations separately. Only literal source-supported labels reach association.
    if label is None:
        return None
    return label if re.search(r'(?<!\w)'+re.escape(label)+r'(?!\w)', native_text) else None


def lines_for(region, inv):
    known = {o['id']:o for o in inv['objects']}
    return [copy.deepcopy(known[oid]) for oid in region['object_ids']
            if known[oid]['type']=='native-text-line']


def body_components(row, decoded, inv, response_hash):
    require(inv['page']==row['page'] and inv['source_sha256']==row['source_sha256'], 'component-source-binding')
    components=[]
    for i, table in enumerate(decoded['mapped']['tables'], 1):
        regions=[]
        for r in decoded['regions']:
            if r['group']!=i:
                continue
            regions.append(dict(id=f'p{row["page"]:04d}-body-{i:03d}-f{r["fragment"]:02d}',
                page=row['page'], bbox=r['bbox'], coordinate_system=pilot.COORD,
                original_member_ids=copy.deepcopy(r['object_ids']), lines=lines_for(r,inv),
                source_members=[copy.deepcopy(next(o for o in inv['objects'] if o['id']==oid)) for oid in r['object_ids']],
                crop=f'{row["directory"]}/body-exports/{r["png"]}'))
        text='\n'.join(line['text'] for r in regions for line in r['lines'])
        components.append(dict(id=f'p{row["page"]:04d}-body-{i:03d}', role='body',
            source_document=row['identity'], source_sha256=row['source_sha256'], page=row['page'],
            regions=regions, native_text=text, model_observed_label=table['label'],
            observed_label=observed_label(table['label'],text), associated_label=None,
            model_uncertainty=copy.deepcopy(table['uncertainty']), response_sha256=response_hash,
            origin='actual-body-response', human_acceptance='pending'))
    return components
