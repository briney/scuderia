"""Optional source locators: exact retained text, never a truth/coverage gate."""
import hashlib
import re

# Unqualified P/L markers always refer to the selected manuscript, not a body alias.
TOKEN=re.compile(r'(?:(s-[0-9a-f]{24})/)?P(\d{1,9}):L(\d{1,9})(?:-(?:P(\d{1,9}):)?L?(\d{1,9}))?')
MARKER=re.compile(r'(?<![\[\\])\[(?:(?:s-[^/\]\s]+/)?P\d+:[^\]\n]*)\](?![ \t]*[\](\[])')
PROTECTED=re.compile(r'(?ms)^##[ \t]+Abstract[ \t]*\n.*?(?=^##[ \t]|\Z)|(`+|~{3,}).*?\1')


def numbered(text,page,start,end):
    """Label original text slices without changing raw character-window accounting."""
    output=[];offset=0
    for number,line in enumerate(text.splitlines(keepends=True),1):
        right=offset+len(line)
        if offset<end and right>start:
            output.append(f'P{page}:L{number} '+text[max(start,offset):min(end,right)].rstrip('\r\n'))
        offset=right
    return '\n'.join(output)


def extract(markdown,job,work):
    from . import workflow as w
    main=next(s for s in job['sources'] if s['role']=='manuscript')
    sources={s['source_id']:s for s in job['sources'] if s['role'] in ('manuscript','body')}
    pages={};rows=[];warnings=[]
    header=re.match(r'\A---\s*\n.*?\n---\s*\n',markdown,re.S)
    start=header.end() if header else 0
    protected=[(m.start(),m.end()) for m in PROTECTED.finditer(markdown,start)]
    last=start;pieces=[markdown[:start]]
    for group in MARKER.finditer(markdown,start):
        if any(a<=group.start()<b for a,b in protected):continue
        context=markdown[last:group.start()]
        # A comma separating adjacent locators belongs to the citation list.
        pieces.append('' if rows and re.fullmatch(r'[ \t]*,[ \t]*',context) else context.rstrip(' \t'))
        for token in group.group()[1:-1].split(','):
            row=dict(marker=token.strip(),draft_start=group.start(),draft_end=group.end(),context=context.strip(),status='unresolved',segments=[])
            match=TOKEN.fullmatch(token.strip())
            if match:
                sid=match[1] or main['source_id'];source=sources.get(sid)
                p,a=int(match[2]),int(match[3]);q=int(match[4] or p);b=int(match[5] or a)
                if source:
                    records={r['page']:r for r in source['text']}
                    # Bound before iterating an untrusted range.
                    if 0<p<=q<=source['pages'] and q-p+1<=len(records) and all(n in records for n in range(p,q+1)):
                        row.update(source_id=sid,source_sha256=source['sha256'])
                        valid=True
                        for n in range(p,q+1):
                            record=records[n];key=(sid,n)
                            if key not in pages:pages[key]=(work/record['key']).read_text().splitlines()
                            lines=pages[key];left=a if n==p else 1;right=b if n==q else len(lines)
                            if not 1<=left<=right<=len(lines):valid=False;break
                            row['segments'].append(dict(page=n,start_line=left,end_line=right,text_sha256=record['sha256'],quote='\n'.join(lines[left-1:right])))
                        if valid:row['status']='located'
                        else:row['segments']=[]
            if row['status']!='located':warnings.append('Citation locator unresolved: '+row['marker'][:160])
            rows.append(row)
        last=group.end()
    pieces.append(markdown[last:]);clean=''.join(pieces)
    if not rows:warnings.append('No optional citation locators supplied; citation coverage is not certified.')
    evidence=dict(schema='manuscript-citations-v1',annotated_sha256=hashlib.sha256(markdown.encode()).hexdigest(),
        policy='Source locations only; neither claim coverage nor scientific entailment is certified.',citations=rows,warnings=warnings)
    return clean,evidence
