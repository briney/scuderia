import copy, json, re, base64
from pathlib import Path
from .io import require, load, SETTINGS
ASSETS=Path(__file__).parent / "assets"

TYPES=('table','algorithm','code','other','uncertain','unknown')


def reporting_disposition(inv):
    """Page-local form structures; never uses document identity, filename or page number."""
    lines=[o for o in inv['objects'] if o['type']=='native-text-line']
    normalized=[re.sub(r'\s+',' ',o['text']).strip().lower() for o in lines]
    joined=' '.join(normalized)
    nature_heading=any(re.fullmatch(r'nature (research|portfolio)\s*\|\s*reporting summary',s) for s in normalized)
    fields=['sample size','data exclusions','replication','randomization','blinding']
    nature_fields=[s for s in fields if s in normalized]
    nature_instructions=('all studies must disclose on these points' in joined and 'study design' in joined)
    mdar_repeats=sum(s.startswith('indicate where provided: page no/section/legend') for s in normalized)
    materials=[s for s in ['newly created materials','antibodies','dna and rna sequences','cell materials','experimental animals','plants and microbes','human research participants'] if s in normalized]
    mdar_instructions='for all that apply, please note where in the manuscript the required information is provided.' in joined
    nature=nature_heading and len(nature_fields)>=4 and nature_instructions
    mdar=mdar_instructions and mdar_repeats>=4 and len(materials)>=4 and normalized.count('n/a')>=4
    family='Nature Reporting Summary' if nature else 'MDAR materials reporting form' if mdar else None
    evidence=[]
    if family:
        needles=['reporting summary','study design','all studies must disclose','for all that apply','indicate where provided']+fields+materials
        evidence=[{k:o[k] for k in ('id','text','bbox')} for o,s in zip(lines,normalized) if any(n in s for n in needles)]
    return dict(disposition='policy-excluded' if family else 'eligible',family=family,scope='physical-page',
        evidence=evidence,criteria=dict(nature_heading=nature_heading,nature_fields=nature_fields,nature_instructions=nature_instructions,
        mdar_repeated_location_prompts=mdar_repeats,mdar_material_headings=materials,mdar_instructions=mdar_instructions),
        retain_complete_pdf=True,scientific_extraction=not bool(family),rule_version='source-form-structure-v1',
        limitation='Conservative native-text form detection; raster-only forms and unrecognized form templates require independent review.')


def label_type(label):
    if not isinstance(label,str): return None
    s=label.strip().lower()
    for kind,pattern in [('figure',r'^(?:(?:extended data|supplementary)\s+)?(?:figure|fig\.)\s+'),('table',r'^(?:(?:extended data|supplementary)\s+)?table\s+'),('algorithm',r'^algorithm\s+'),('data-file',r'^(?:caption for )?data file\s+')]:
        if re.search(pattern,s): return kind
    return None


def compatible_caption(content_type,label):
    kind=label_type(label)
    if kind is None or content_type in ('unknown','uncertain','other',None): return None
    return kind==content_type


def printed_labels(text):
    return [m.group(0) for m in re.finditer(r'(?<!\w)(?:(?:Extended Data|Supplementary)\s+)?(?:Figure|Fig\.|Table|Algorithm|Data file)\s+(?:S?\d+[A-Za-z]?)(?!\w)',text)]


def classifier_request(root,row,candidates):
    root=Path(root)
    def path(name): return root/name
    require(bool(candidates),'no-candidate-request-forbidden')
    require(len({c['id'] for c in candidates})==len(candidates),'duplicate-input-candidate')
    require(all(c['source_document']==row['identity'] and c['page']==row['page'] for c in candidates),'classifier-page-scope')
    out=path(row['directory']); inv=load(out/'inventory.json')
    # The source page's literal text includes external titles/notes. All original
    # context images are retained because raster headings may lack native text.
    native=[{k:o[k] for k in ('id','page','bbox','text')} for o in inv['objects'] if o['type']=='native-text-line']
    clean=[dict(candidate_id=c['id'],role='body',regions=[dict(page=r['page'],bbox=r['bbox'],coordinate_system=r['coordinate_system'],
        native_lines=[{k:l[k] for k in ('id','page','bbox','text')} for l in r['lines']]) for r in c['regions']]) for c in candidates]
    data=dict(physical_page=row['page'],candidates=clean,native_page_lines=native)
    content=[dict(type='text',text=(ASSETS/'classifier-prompt.txt').read_text()+'\nSOURCE EVIDENCE\n'+json.dumps(data,ensure_ascii=False,separators=(',',':')))]
    for c in candidates:
        for i,r in enumerate(c['regions'],1):
            content.extend([dict(type='text',text=f'Candidate {c["id"]}, original-PDF crop fragment {i}'),
                dict(type='image_url',image_url=dict(url='data:image/png;base64,'+base64.b64encode(path(r['crop']).read_bytes()).decode()))])
    old=load(out/'original-wire.json')
    content.extend(copy.deepcopy(old['messages'][0]['content'][1:]))
    return dict(SETTINGS,messages=[dict(role='user',content=content)])


def classify_validate(value,candidates):
    require(isinstance(value,dict) and set(value)=={'classifications'},'classification-root-schema')
    require(isinstance(value['classifications'],list),'classification-list')
    require(len({(c['source_document'],c['page']) for c in candidates})<=1,'classifier-page-scope')
    known={c['id'] for c in candidates}; require(len(known)==len(candidates),'duplicate-input-candidate'); seen=set()
    for item in value['classifications']:
        require(isinstance(item,dict) and set(item)=={'candidate_id','content_type','source_label','label_evidence','uncertainty'},'classification-item-schema')
        ident=item['candidate_id']; require(isinstance(ident,str) and ident in known and ident not in seen,'classification-candidate-accounting'); seen.add(ident)
        require(item['content_type'] in TYPES,'content-type')
        uncertainty=item['uncertainty']; require(isinstance(uncertainty,list) and all(isinstance(s,str) and s.strip() for s in uncertainty),'classification-uncertainty')
        require(item['content_type'] not in ('unknown','uncertain') or bool(uncertainty),'uncertain-needs-reason')
        label=item['source_label']; require(label is None or isinstance(label,str) and label.strip(),'source-label')
        require(item['label_evidence'] in ('crop-image','context-image','native-text','none'),'label-evidence')
        require((label is None)==(item['label_evidence']=='none'),'label-evidence-presence')
        require(compatible_caption(item['content_type'],label) is not False,'source-label-type-incompatible')
    require(seen==known,'classification-omitted-candidates')
    return dict(status='passed',candidate_count=len(candidates),assigned_once=sorted(seen),
        semantics='Model content classification and model-observed labels; independent visual verification pending. No association or geometry change.')
