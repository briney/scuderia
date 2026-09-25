"""Read-time bindings shared by import, count, seal, execute and report."""
from pathlib import Path
from .io import require, load, sha, safe, digest, dumps
from . import trusted
from .requests import SETTINGS


def request(run, row):
    p=safe(run,row['directory'])
    for name,key,label in (('source-evidence.json','evidence_sha256','evidence-binding'),
                           ('request-wire.json','request_sha256','request-binding'),
                           ('prompt.txt','prompt_sha256','prompt-binding')):
        require(sha(p/name)==row[key],label+':'+row['id'])
    evidence=load(p/'source-evidence.json'); wire=load(p/'request-wire.json')
    require(evidence['element_id']==row['element_id'] and evidence['source_document']==row['document'] and
            evidence['source_sha256']==row['source_sha256'], 'evidence-identity-binding')
    require(bool(evidence.get('caption_only'))==row['caption_only'],'variant-binding')
    require({k:v for k,v in wire.items() if k!='messages'}==SETTINGS,'pinned-settings-binding')
    require(wire['messages'][0]['content'][0]['text'].startswith((p/'prompt.txt').read_text()),'wire-prompt-binding')
    if row['caption_only']:
        require(not evidence['body_fragments'] and all(x['type']=='text' for x in wire['messages'][0]['content']), 'caption-only-input-binding')
    return evidence,wire


def verify(run, *, for_execution=True):
    from .package_io import SourcePackage
    from .accounting import accounting
    run=Path(run).absolute()
    require(sha(run/'enrichment-plan.json')==(run/'plan.sha256').read_text(), 'plan-binding')
    plan=load(run/'enrichment-plan.json')
    # The reader supports these semantics, not arbitrary schemas with similar fields.
    require((plan.get('schema'), plan.get('stage'), plan.get('prompt_version'), plan.get('response_schema')) ==
            ('pdf-source-package-enrichment-v7', 'enrichment-prepare-v7',
             'enrichment-prompts-v7', 'enrichment-response-v7'), 'unsupported-enrichment-format')
    require(plan.get('settings') == SETTINGS and plan.get('model') == SETTINGS['model'], 'unsupported-enrichment-settings')
    trusted.validate_code_provenance(plan['code'])
    trusted.validate_code_provenance(plan['method']['code'])
    if for_execution:
        require(plan['code']==trusted.code_hashes(),'enrichment-code-changed')
        require(plan['method']['code']==trusted.method_hashes(plan['method']['root']),'accepted-method-code-changed')
    method = plan['method']['root'] if for_execution else trusted.read_method_path()
    require(not run.resolve().is_relative_to(Path(plan['source_package']['root']).resolve()),'output-inside-source-forbidden')
    accounting(plan,{})
    # Check small request evidence first; hash/revalidate the source only once per operation.
    for row in plan['requests']:
        if row.get('id'): request(run,row)
    pkg=SourcePackage(plan['source_package']['root'],method=method)
    require(pkg.snapshot['tree_sha256']==plan['source_package']['tree_sha256'],'source-package-changed')
    elements={e['id']:e for d in pkg.documents for e in d['elements']}
    for row in plan['requests']:
        if row.get('id'):
            require(row['element_id'] in elements and digest(dumps(elements[row['element_id']]))==row['element_sha256'],'source-element-changed')
            from .requests import build_request, PROMPTS, FIGURE_PROMPT_CAPTION_ONLY
            wire, evidence = build_request(pkg, pkg.doc(row['document']), elements[row['element_id']],
                                           row['kind'], caption_only=row['caption_only'])
            saved_evidence, saved_wire = request(run, row)
            prompt = FIGURE_PROMPT_CAPTION_ONLY if row['caption_only'] else PROMPTS[row['kind']]
            require((saved_wire, saved_evidence) == (wire, evidence) and
                    (safe(run, row['directory'])/'prompt.txt').read_text() == prompt,
                    'incompatible-enrichment-payload-semantics')
    return plan
