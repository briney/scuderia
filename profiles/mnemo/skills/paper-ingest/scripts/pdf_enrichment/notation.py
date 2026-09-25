"""Attributed text runs, not mathematical parsing or independent validation.

Never alter raw strings. Offset roles are explicit declarations. Native geometry
can corroborate a declared vertical displacement; font size alone cannot. Missing
or complex notation stays unverified/unresolved. Visual roles remain model claims.
"""
import html
import math
from .io import require
from .references import image_refs


def _geometry(run, sources):
    """Bind a run to ONE copied native span and its same-line baseline span."""
    matches=[]
    for source in sources:
        if 'line_id' not in source:
            continue
        # A line may contribute disjoint pieces. Bind against the piece owning
        # this output range before checking its retained (whole-line) spans.
        if not source['output_start'] <= run['start'] < run['end'] <= source['output_end']:
            continue
        spans=source.get('native_spans',[])
        for span in spans:
            if span.get('span_id') != run['source_ref']:
                continue
            baselines=[s for s in spans if s.get('span_id')==run.get('baseline_span_ref')]
            require(len(baselines)==1 and baselines[0] is not span, 'notation-geometry-baseline')
            baseline=baselines[0]
            start,end=span.get('start'),span.get('end')
            require(type(start) is int and type(end) is int and source['start'] <= start < end <= source['end'], 'notation-geometry-range')
            require(run['start']==source['output_start']+start-source['start'] and
                    run['end']==source['output_start']+end-source['start'] and
                    run['text']==span.get('text'), 'notation-geometry-text-offset')
            # A small, displaced span plus a named baseline, not a font-size classifier.
            values=[span.get('size'),baseline.get('size')]
            for s in (span,baseline):
                origin=s.get('origin')
                require(isinstance(origin,(list,tuple)) and len(origin)==2, 'notation-geometry-origin')
                values.extend(origin)
            require(all(type(v) in (int,float) and math.isfinite(v) for v in values), 'notation-geometry-finite')
            require(0 < span['size'] < baseline['size'] and
                    span['origin'][0] >= baseline['origin'][0], 'notation-geometry-size-position')
            delta=span['origin'][1]-baseline['origin'][1]
            require(delta < 0 if run['role']=='superscript' else delta > 0, 'notation-geometry-displacement')
            matches.append(dict(line_id=source['line_id'],fragment_id=source['fragment_id'],page=source['page'],
                                span=span,baseline_span=baseline,offset_basis=source['offset_basis']))
    require(len(matches)==1, 'notation-geometry-source-not-unique')
    return matches[0]


def selected_roles(evidence, declaration, raw, sources):
    """Assemble offsets and crop ownership, then use the strict attributed-run checks."""
    from .copy_rules import fragment_line_index, selected_range
    require(set(declaration)=={'status','roles','unresolved'}, 'notation-role-keys')
    require(isinstance(declaration['roles'],list), 'notation-roles')
    require(isinstance(declaration['unresolved'],list) and all(isinstance(s,str) and s.strip() for s in declaration['unresolved']), 'notation-unresolved')
    require(sources and all('line_id' in s for s in sources), 'notation-roles-native-only')
    index=fragment_line_index(evidence); runs=[]; unresolved=list(declaration['unresolved']); selected=[]
    for role in declaration['roles']:
        keys={'selector','role','basis'}
        require(isinstance(role,dict) and keys <= set(role) <= keys|{'baseline_span_ref'}, 'notation-role-keys')
        require(role['role'] in ('superscript','subscript'), 'notation-role')
        require(role['basis'] in ('crop-image','native-geometry'), 'notation-role-basis')
        require(('baseline_span_ref' in role)==(role['basis']=='native-geometry'), 'notation-role-baseline')
        if role['basis']=='native-geometry':
            require(isinstance(role['selector'],dict) and set(role['selector'])=={'span_id'}, 'notation-role-geometry-needs-span')
        mapped=selected_range(role['selector'],raw,sources,index)
        if mapped is None:
            unresolved.append('Native selector cannot map exactly to copied output: '+str(role['selector']))
            continue
        a,b=mapped['start'],mapped['end']
        run=dict(start=a,end=b,text=raw[a:b],role=role['role'],basis=role['basis'],
                 source_ref=role['selector']['span_id'] if role['basis']=='native-geometry' else mapped['source']['fragment_id'])
        if 'baseline_span_ref' in role: run['baseline_span_ref']=role['baseline_span_ref']
        runs.append(run); selected.append((a,b,role['selector']))
    crops=list(dict.fromkeys(s['fragment_id'] for s in sources))
    normalized=dict(status=declaration['status'],source_refs=crops,runs=sorted(runs,key=lambda r:(r['start'],r['end'])),unresolved=unresolved)
    result=assemble(evidence,normalized,raw,sources,present=True)
    for run in result['runs']:
        run['selector']=next(sel for a,b,sel in selected if (a,b)==(run['start'],run['end']))
    result['declaration']=declaration
    result['assembly']='code-mapped-native-selectors'
    return result


def assemble(evidence, declaration, raw, sources, *, present=False):
    if not present:
        return dict(status='unverified',runs=[],unresolved=['No notation declaration; literal text does not establish typography.'],
                    scientific_review='pending')
    require(isinstance(raw,str), 'notation-needs-literal-text')
    if isinstance(declaration,dict) and 'roles' in declaration:
        return selected_roles(evidence,declaration,raw,sources)
    require(isinstance(declaration,dict) and set(declaration)=={'status','source_refs','runs','unresolved'}, 'notation-keys')
    require(declaration['status'] in ('resolved','unresolved','unverified'), 'notation-status')
    require(isinstance(declaration['runs'],list), 'notation-runs')
    unresolved=declaration['unresolved']
    require(isinstance(unresolved,list) and all(isinstance(s,str) and s.strip() for s in unresolved), 'notation-unresolved')
    crops=image_refs(evidence,declaration['source_refs'])
    allowed={s.get('fragment_id',s.get('source_ref')) for s in sources}
    require(set(declaration['source_refs']) <= allowed, 'notation-crop-outside-content-sources')
    runs=[]; end=0
    for run in declaration['runs']:
        keys={'start','end','text','role','basis','source_ref'}
        require(isinstance(run,dict) and keys <= set(run) <= keys | {'baseline_span_ref'}, 'notation-run-keys')
        a,b=run['start'],run['end']
        require(type(a) is int and type(b) is int and end <= a < b <= len(raw), 'notation-range-or-overlap')
        require(isinstance(run['text'],str) and raw[a:b]==run['text'], 'notation-exact-substring')
        require(run['role'] in ('superscript','subscript'), 'notation-role')
        require(run['basis'] in ('crop-image','native-geometry'), 'notation-basis')
        if run['basis']=='crop-image':
            require('baseline_span_ref' not in run and run['source_ref'] in declaration['source_refs'], 'notation-visual-source')
            # A native slice must belong to this crop, including its exact output range.
            native=[s for s in sources if 'line_id' in s]
            if native:
                require(any(s['fragment_id']==run['source_ref'] and s['output_start'] <= a < b <= s['output_end'] for s in native), 'notation-visual-range-source')
            source=next(c for c in crops if c['source_ref']==run['source_ref'])
        else:
            source=_geometry(run,sources)
            require(source['fragment_id'] in declaration['source_refs'], 'notation-geometry-crop')
        runs.append(dict(run,source=source))
        end=b
    return dict(status='unresolved' if unresolved else declaration['status'], declared_status=declaration['status'],
                source_refs=crops,runs=runs,unresolved=unresolved,scientific_review='pending',
                offset_basis='Unicode code points into unchanged raw_value/text, after explicit joins; end exclusive')


def literal_mathematics(text, declaration, sources):
    """Retain literal LaTeX source and MODEL attribution; never execute TeX."""
    require(isinstance(text,str) and text.strip(), 'latex-text-required')
    require(isinstance(declaration,dict) and set(declaration)=={'status','unresolved'}, 'latex-notation-keys')
    require(declaration['status'] in ('resolved','unresolved'), 'latex-notation-status')
    gaps=declaration['unresolved']
    require(isinstance(gaps,list) and all(isinstance(s,str) and s.strip() for s in gaps), 'latex-unresolved')
    return dict(status='unresolved' if gaps else declaration['status'],declared_status=declaration['status'],
                unresolved=gaps,runs=[],source_refs=sources,scientific_review='pending',
                basis='crop-image-model-transcription',representation='latex-source',
                display='escaped-literal-source-no-TeX-execution',source_fidelity='not-independently-verified')


def render(raw, notation=None, *, as_html=False):
    """Readable roles with explicit status; raw CSV/JSON is separate."""
    notation=notation or {'status':'unverified','runs':[]}
    escape=html.escape if as_html else str
    raw='' if raw is None else raw
    out=[]; pos=0
    for run in notation.get('runs',[]):
        out.append(escape(raw[pos:run['start']]))
        text=escape(raw[run['start']:run['end']])
        if as_html:
            tag='sup' if run['role']=='superscript' else 'sub'
            out.append('<'+tag+'>'+text+'</'+tag+'>')
        else:
            out.append(('^{' if run['role']=='superscript' else '_{')+text+'}')
        pos=run['end']
    out.append(escape(raw[pos:]))
    if notation['status']!='resolved':
        out.append(' [notation-'+escape(notation['status'])+']')
    return ''.join(out)
