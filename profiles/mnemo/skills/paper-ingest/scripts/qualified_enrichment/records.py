"""Source-bound target indexing and uncertainty projection (no inference)."""
import hashlib
import json


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False,
                                     allow_nan=False, separators=(',', ':')).encode()).hexdigest()


def require(ok, reason):
    if not ok:
        raise ValueError(reason)


def nodes(value, path=''):
    result = {path: value}
    if isinstance(value, dict):
        for key, item in value.items():
            result.update(nodes(item, path+'/'+key.replace('~', '~0').replace('/', '~1')))
    elif isinstance(value, list):
        for index, item in enumerate(value):
            result.update(nodes(item, path+'/'+str(index)))
    return result


def resolve_pointer(value, path):
    require(isinstance(path, str) and (path == '' or path.startswith('/')), 'nonexistent-target')
    current = value
    for token in path.split('/')[1:] if path else []:
        token = token.replace('~1', '/').replace('~0', '~')
        if isinstance(current, list):
            require(token.isdecimal() and str(int(token)) == token and int(token) < len(current), 'nonexistent-target')
            current = current[int(token)]
        else:
            require(isinstance(current, dict) and token in current, 'nonexistent-target')
            current = current[token]
    return current


def related(left, right):
    return left == right or left.startswith(right+'/') or right.startswith(left+'/')


def finding(element, target, category, reason, *, stage='extraction', provenance=None, evidence=None):
    resolve_pointer(element['outcome'], target)
    value = dict(element_id=element['element_id'], source_sha256=element['source_sha256'],
                 target=target, category=category, reason=reason, stage=stage,
                 provenance=provenance or {'kind': 'deterministic-check', 'check': 'v7-state-projection-v1'},
                 evidence=evidence or [], status='unresolved')
    value['id'] = digest(value)
    return value


def project(element):
    """Project explicit saved states; this is not a character-loss classifier."""
    findings = []
    uncertain = {'partial', 'unresolved', 'unverified', 'unknown', 'unreadable',
                 'unsupported', 'failed', 'interrupted', 'prepared-not-sent',
                 'source-incomplete', 'not-selected', 'unknown-type', 'incomplete', 'missing', 'unavailable'}
    lists = {'unresolved', 'unresolved_symbols', 'missing', 'coverage_warnings',
             'element_warnings', 'gaps', 'layout_uncertainties', 'limitations'}
    for path, value in nodes(element['outcome']).items():
        if not isinstance(value, dict):
            continue
        # Bind each state to its containing cell, statement, observation or
        # metadata block, not to a detached global warning summary.
        reasons = []
        for key, item in value.items():
            if isinstance(item, str) and (key in ('status', 'grouping') or key.endswith('_status')) and item in uncertain:
                reasons.append(key+': '+item)
            elif key == 'indent' and item is None and value.get('layout_version'):
                reasons.append('indent: unknown saved native layout')
            elif key in lists and item:
                reasons.append(key+': '+json.dumps(item, ensure_ascii=False))
            elif key in ('unreadable', 'unresolved') and item is True:
                reasons.append(key+': true')
            elif key == 'text_verification' and isinstance(item, str) and item.startswith('unverified'):
                reasons.append(key+': '+item)
        if reasons:
            findings.append(finding(element, path, 'saved-uncertainty', '; '.join(reasons)))
    warnings = element.get('source_element', {}).get('coverage_warnings', [])
    if warnings:
        findings.append(finding(element, '', 'source-coverage', json.dumps(warnings, ensure_ascii=False)))
    for item in findings:
        if item['reason'] == 'status: partial' and any(
                other['target'].startswith(item['target']+'/') for other in findings if other is not item):
            item['summary_only'] = True
    if element['outcome'].get('status') == 'failed':
        require(not element['outcome'].get('record'), 'failed-outcome-cannot-have-accepted-record')
    return dict(element_id=element['element_id'], source_sha256=element['source_sha256'],
                outcome=element['outcome'], evidence=element['evidence'],
                source_element=element.get('source_element'), source_pdf=element.get('source_pdf'),
                content_type=element.get('content_type'),
                findings=findings, coverage=[], review_status='unreviewed')
