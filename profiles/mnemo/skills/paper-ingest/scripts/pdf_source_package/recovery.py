"""Offline material policy: omit only structurally valid explicit empty placeholders.

The strict decoder and source exporter are copied without edits. All nonempty
records are decoded together, preserving cross-record membership validation.
Indices below are zero-based source response indices; region groups remain
one-based, including gaps left by omitted placeholders.
"""


import copy


from . import material


from .components_base import body_components


from .io import require


from .table_model import decode, DecodeError


POLICY_VERSION = 'explicit-empty-fragment-placeholder-v1'


def decode_selection(value, inv, mapping):
    require(isinstance(value, dict), 'selection-container')
    keys = [k for k in ('blocks', 'tables') if k in value]
    require(len(keys) == 1, 'selection-record-container')
    key = keys[0]
    internal = copy.deepcopy(value)
    if key == 'blocks':
        internal['tables'] = internal.pop('blocks')
    require(set(internal) in ({'status', 'tables'}, {'status', 'tables', 'uncertainty'}), 'selection-root-shape')
    require(isinstance(internal['tables'], list), 'record-list-required')
    omitted = []
    retained = []
    for index, record in enumerate(internal['tables']):
        require(isinstance(record, dict) and set(record) == {'label', 'fragments', 'uncertainty'}, 'record-schema')
        require(record['label'] is None or isinstance(record['label'], str) and bool(record['label'].strip()), 'label-schema')
        uncertainty = record['uncertainty']
        require(isinstance(uncertainty, list) and all(isinstance(s, str) and s.strip() for s in uncertainty), 'record-uncertainty-schema')
        require(isinstance(record['fragments'], list), 'fragment-list-required')
        (retained if record['fragments'] else omitted).append(index)
    # Empty/unresolved status handling is unchanged; this tolerance is for ok only.
    if omitted:
        require(internal['status'] == 'ok', 'placeholder-policy-requires-ok')
    validator = copy.deepcopy(internal)
    validator['tables'] = [validator['tables'][i] for i in retained]
    if omitted and not retained:
        # Internal validation only: validate root metadata and inventory binding.
        # This is not a model-reported empty status and is never raw output.
        validator['status'] = 'empty'
    if omitted and not retained:
        compatibility = copy.deepcopy(validator)
        compatibility.setdefault('uncertainty', [])
        result = decode(compatibility, inv, mapping)
        result.update(root_uncertainty_present='uncertainty' in internal,
                      model_root_uncertainty=copy.deepcopy(internal.get('uncertainty')),
                      root_metadata_disposition='provided' if 'uncertainty' in internal else 'NOT PROVIDED')
        if 'uncertainty' not in internal:
            result['warnings'].append(dict(kind='missing-root-uncertainty',
                meaning='NOT PROVIDED, not model-reported empty uncertainty', geometry_changed=False))
    else:
        result = material.decode_body(validator, inv, mapping)
    result['validator_input'] = validator
    result['raw_selection'] = copy.deepcopy(value)
    result['raw_alias_selection'] = internal
    result['material_policy_version'] = POLICY_VERSION
    result['record_container'] = key
    result['retained_record_indexes'] = retained
    result['omitted_record_indexes'] = omitted
    result['export_outcome'] = ('no-export-all-empty-placeholders' if omitted and not retained else
                                'exportable' if result['regions'] else 'no-export-original-status')
    if omitted:
        try:
            decode(internal, inv, mapping)
            original = dict(status='passed')
        except DecodeError as exc:
            original = dict(status='rejected', reason=str(exc), evidence=copy.deepcopy(exc.evidence))
        result['original_strict_diagnostic'] = original
        mapped = copy.deepcopy(internal)
        for compact_index, source_index in enumerate(retained):
            mapped['tables'][source_index] = result['mapped']['tables'][compact_index]
        mapped['uncertainty'] = result['model_root_uncertainty']
        result['mapped'] = mapped
        for region in result['regions']:
            region['group'] = retained[region['group'] - 1] + 1
            region['png'] = f'table-{region["group"]:03d}-fragment-{region["fragment"]:02d}.png'
        for warning in result['warnings']:
            if 'table' in warning:
                warning['table'] = retained[warning['table'] - 1] + 1
        result['warnings'].extend(dict(kind='empty-fragment-list-placeholder',
            original_record_index=i, record=copy.deepcopy(internal['tables'][i]),
            geometry_changed=False, meaning='Explicit empty list omitted from export; not a classified or exported candidate')
            for i in omitted)
    return result


def components(row, decoded, inv, response_hash, *, origin) -> list[dict]:
    # The existing component constructor uses one-based mapped-list positions.
    # Retaining placeholders in mapped preserves IDs; empty components never export.
    return [dict(c, original_record_index=i, material_policy_version=POLICY_VERSION,
                 extraction_origin=origin,
                 human_acceptance='pending')
            for i, c in enumerate(body_components(row, decoded, inv, response_hash))
            if i in decoded['retained_record_indexes']]
