"""Private table decoder. No mutation of the frozen figure validator/exporter."""


import sys


sys.dont_write_bytecode = True


import copy


import math


from . import native as pilot, grouping
from .io import require


class DecodeError(ValueError):
    def __init__(self, message, evidence):
        super().__init__(message)
        self.evidence=evidence


def as_figures(mapped):
    """Internal key-only adapter for frozen geometry/export; no figure inference."""
    return dict(status=mapped['status'], figures=copy.deepcopy(mapped['tables']), uncertainty=copy.deepcopy(mapped['uncertainty']))


def decode(value, inv, mapping):
    result=dict(raw_alias_selection=copy.deepcopy(value),mapped=None,regions=[],warnings=[],strict_diagnostic=None)
    try:
        require(isinstance(value,dict) and set(value)=={'status','tables','uncertainty'},'table-root-schema')
        require(value['status'] in ('ok','empty','unresolved'),'status-schema')
        def uncertainty(x):
            return isinstance(x,list) and all(isinstance(s,str) and s.strip() for s in x)
        require(uncertainty(value['uncertainty']),'root-uncertainty-schema')
        require(isinstance(value['tables'],list),'tables-schema')
        require(value['status']!='empty' or not value['tables'],'empty-with-tables')
        require(value['status']!='ok' or bool(value['tables']),'ok-without-tables')
        require(value['status']!='unresolved' or bool(value['uncertainty']),'unresolved-without-reason')
        require(mapping['page']==inv['page'],'mapping-wrong-page')
        known={o['id']:o for o in inv['objects']}
        require(len(known)==len(inv['objects']),'ambiguous-inventory')
        if 'units' in mapping:
            grouping.verify_partition(inv,mapping)
            members=[u['members'] for u in mapping['units']]
        else:
            require(mapping['native_ids']==[o['id'] for o in inv['objects']],'mapping-not-bound')
            members=[[oid] for oid in mapping['native_ids']]
        mapped=copy.deepcopy(value)
        result['mapped']=mapped
        seen={}
        for gi,table in enumerate(mapped['tables']):
            require(isinstance(table,dict) and set(table)=={'label','fragments','uncertainty'},'table-schema')
            require(table['label'] is None or isinstance(table['label'],str) and table['label'].strip(),'label-schema')
            require(uncertainty(table['uncertainty']),'table-uncertainty-schema')
            require(isinstance(table['fragments'],list) and table['fragments'],'fragments-schema')
            for fi,frag in enumerate(table['fragments']):
                require(isinstance(frag,dict) and set(frag)=={'object_ids'},'fragment-schema')
                aliases=frag['object_ids']
                require(isinstance(aliases,list) and aliases,'empty-or-ambiguous-selection')
                expanded=[]
                for alias in aliases:
                    require(type(alias) is int,'non-integer-alias')
                    require(1<=alias<=len(members),'unknown-or-out-of-range-alias')
                    expanded.extend(members[alias-1])
                frag['object_ids']=expanded
                for oid in expanded:
                    obj=known[oid]
                    require(oid.startswith(f'p{inv["page"]:04d}-') and obj.get('page',inv['page'])==inv['page'],'wrong-page-member')
                    if oid in seen:
                        require(seen[oid]==(gi,fi),'ambiguous-reuse-across-fragments-or-tables')
                        result['warnings'].append(dict(kind='duplicate-id',id=oid,table=gi+1,fragment=fi+1))
                    seen[oid]=(gi,fi)
                    b=obj['bbox']
                    require(isinstance(b,list) and len(b)==4 and all(type(v) in (int,float) and math.isfinite(v) for v in b),'nonfinite-or-malformed-bounds')
                    require(b[0]<=b[2] and b[1]<=b[3],'inverted-bounds')
                    zero=b[0]==b[2] or b[1]==b[3]
                    allowed={'out-of-page-bounds'} | ({'degenerate-or-inverted-bounds'} if zero else set())
                    require(all(i in allowed for i in obj['issues']),'unsupported-member-issues')
                    require(obj['selectable'] is True or zero and obj['issues']==['degenerate-or-inverted-bounds'] or zero and set(obj['issues'])==allowed,'nonselectable-member')
                    if zero:
                        result['warnings'].append(dict(kind='zero-area-member-included-in-extrema',id=oid,bbox=b,table=gi+1,fragment=fi+1))
                    if 'out-of-page-bounds' in obj['issues']:
                        result['warnings'].append(dict(kind='page-edge-clipping',id=oid,bbox=b))
                b=pilot.union([known[oid]['bbox'] for oid in expanded])
                require(b[0]<b[2] and b[1]<b[3],'nonpositive-fragment-union')
        adapter=as_figures(mapped)
        try:
            pilot.validate(adapter,inv)
            result['strict_diagnostic']={'status':'passed','scope':'old figure schema via tables-to-figures key adapter; not table correctness'}
        except ValueError as exc:
            result['strict_diagnostic']={'status':'rejected','reason':str(exc),'scope':'diagnostic only; material table policy applied separately'}
        regions=pilot.selected_regions(adapter,inv)
        for r in regions:
            r['table_union_bbox']=r.pop('figure_union_bbox')
            r['png']=f'table-{r["group"]:03d}-fragment-{r["fragment"]:02d}.png'
        result['regions']=regions
        return result
    except (ValueError,KeyError,TypeError,IndexError) as exc:
        raise DecodeError(str(exc),result) from exc
