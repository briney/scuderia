"""Narrow metadata-omission interpretation; the frozen decoder and renderer are unchanged."""


import sys


sys.dont_write_bytecode = True


import copy


from .components_base import body_components
from .io import require


from .table_model import decode, DecodeError


def interpret(value, inv, mapping):
    require(isinstance(value,dict) and value.get('status')=='ok','material-requires-ok-body')
    present='uncertainty' in value
    require(set(value)==({'status','tables','uncertainty'} if present else {'status','tables'}),'material-root-shape')
    original=copy.deepcopy(value)
    try:
        strict=decode(value,inv,mapping)
        original_diagnostic=dict(status='passed')
    except DecodeError as exc:
        original_diagnostic=dict(status='rejected',reason=str(exc),evidence=copy.deepcopy(exc.evidence))
        require(not present and str(exc)=='table-root-schema','not-the-permitted-metadata-omission')
        # Parser-internal compatibility only. This view is never persisted as raw.
        compatibility=copy.deepcopy(value)
        compatibility['uncertainty']=[]
        strict=decode(compatibility,inv,mapping)
    result=copy.deepcopy(strict)
    result['raw_alias_selection']=original
    result['mapped']['uncertainty']=copy.deepcopy(value['uncertainty']) if present else None
    result['root_uncertainty_present']=present
    result['model_root_uncertainty']=copy.deepcopy(value['uncertainty']) if present else None
    result['root_metadata_disposition']='provided' if present else 'NOT PROVIDED'
    result['geometry_subtree_strict_diagnostic']=result.pop('strict_diagnostic')
    result['original_strict_diagnostic']=original_diagnostic
    result['compatibility_view_used']=not present
    if not present:
        result['warnings'].append(dict(kind='missing-root-uncertainty',meaning='NOT PROVIDED, not model-reported empty uncertainty',geometry_changed=False))
    require(value==original,'raw-selection-mutated')
    return result


def decode_body(value, inv, mapping):
    # Empty and unresolved statuses keep the original frozen handling.
    if not isinstance(value, dict) or value.get('status')!='ok':
        return decode(value, inv, mapping)
    try:
        return interpret(value, inv, mapping)
    except ValueError as exc:
        # A policy rejection must still retain the diagnostic on the exact raw
        # selection, not pass a temporary compatibility view off as model output.
        try:
            decode(value, inv, mapping)
            original=dict(status='passed')
        except DecodeError as strict:
            original=dict(status='rejected',reason=str(strict),evidence=copy.deepcopy(strict.evidence))
        evidence=dict(raw_alias_selection=copy.deepcopy(value),original_strict_diagnostic=original,
                      material_policy_diagnostic=str(exc),root_uncertainty_present='uncertainty' in value,
                      model_root_uncertainty=copy.deepcopy(value.get('uncertainty')))
        if isinstance(exc,DecodeError):
            evidence['geometry_subtree_diagnostic']=copy.deepcopy(exc.evidence)
            evidence['geometry_subtree_diagnostic']['raw_alias_selection']=copy.deepcopy(value)
            if 'uncertainty' not in value and evidence['geometry_subtree_diagnostic'].get('mapped') is not None:
                evidence['geometry_subtree_diagnostic']['mapped']['uncertainty']=None
        raise DecodeError(str(exc),evidence) from exc


def components(row,result,inv,response_hash):
    output=body_components(row,result,inv,response_hash)
    for candidate in output:
        candidate.update(
            root_uncertainty_present=result.get('root_uncertainty_present', True),
            model_root_uncertainty=result.get('model_root_uncertainty', result['mapped']['uncertainty']),
            root_metadata_disposition=result.get('root_metadata_disposition', 'provided'),
            material_interpretation_policy='material-policy.json',
            original_strict_diagnostic=result.get('original_strict_diagnostic', result.get('strict_diagnostic')),
            geometry_subtree_strict_diagnostic=result.get('geometry_subtree_strict_diagnostic', result.get('strict_diagnostic')),
            metadata_presence_warnings=[copy.deepcopy(w) for w in result['warnings'] if w['kind']=='missing-root-uncertainty'])
    return output
