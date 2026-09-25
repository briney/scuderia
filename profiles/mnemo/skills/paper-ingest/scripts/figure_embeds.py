"""Local Markdown figure embeds from retained final products; never copies images."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
from urllib.parse import quote, unquote

import portable_articles as pa
from article_runtime import absolute, require

PATTERN = re.compile(r'<!-- paper-figure (\{[^\n]*\}) -->\n([\s\S]*?)<!-- /paper-figure -->\n')


def digest(text):
    return hashlib.sha256(text.encode()).hexdigest()


def escape(text):
    return re.sub(r'([\\`*_{}\[\]<>#!|])', r'\\\1', ' '.join(str(text).split()))


def blocks(text):
    matches=list(PATTERN.finditer(text))
    require(text.count('<!-- paper-figure ')==len(matches) and text.count('<!-- /paper-figure -->')==len(matches), 'malformed-figure-block')
    values=[(json.loads(m[1]),m[2]) for m in matches]
    require(len({v[0]['element_id'] for v in values})==len(values),'duplicate-figure-block')
    for metadata,body in values:
        require(metadata['sha256']==digest(body),'figure-block-edited: reconcile manual edits before regenerating')
    return values


def role(element,manifest):
    value=next(d.get('source_role') for d in manifest['documents'] if d['identity']==element['document'])
    require(value in ('manuscript','supplement'),'figure-source-role-unresolved')
    return value


def figure(element,manifest,page,image_root,*,reason):
    label=element['label'] or element['element_id']
    parts=['**'+escape(label)+'**\n\n']
    if reason: parts.append('Supplementary figure — '+escape(reason)+'\n\n')
    fragments=element['evidence'].get('body_fragments',[])
    for i,fragment in enumerate(fragments):
        relative=os.path.relpath(absolute(image_root)/fragment['crop'],absolute(page).parent)
        alt=label+(f' (part {i+1} of {len(fragments)})' if len(fragments)>1 else '')
        parts.append('!['+escape(alt)+']('+quote(relative,safe='/.-_~')+')\n\n')
    if not fragments: parts.append('Figure image unavailable: no retained body crop.\n\n')
    captions=list(dict.fromkeys(c.get('native_text','').strip() for c in element['evidence'].get('captions',[]) if c.get('native_text','').strip()))
    for caption in captions: parts.append('**Source caption:** '+escape(caption)+'\n\n')
    return ''.join(parts)


def render(text,manifest,page,*,image_root=None,supplements=None):
    import final_products as fp
    m=fp.verify(manifest);image_root=absolute(image_root or absolute(manifest).parent)
    previous={meta['element_id']:(meta,body) for meta,body in blocks(text)}
    selected={eid:meta.get('reason','') for eid,(meta,_) in previous.items() if meta.get('reason')}
    require(supplements is None or isinstance(supplements,dict),'supplement-mapping-required')
    selected.update(supplements or {})
    index={e['element_id']:e for e in m['elements']}
    for eid,reason in selected.items():
        require(eid in index and index[eid]['kind']=='figure' and role(index[eid],m)=='supplement','supplement-figure-required')
        require(isinstance(reason,str) and reason.strip(),'supplement-reason-required')
    figures=[e for e in m['elements'] if e['kind']=='figure' and (role(e,m)=='manuscript' or e['element_id'] in selected)]
    require(set(previous)<={e['element_id'] for e in figures},'previous-figure-no-longer-present: reconcile before regeneration')
    rendered={}
    for e in figures:
        reason=selected.get(e['element_id'],'');body=figure(e,m,page,image_root,reason=reason)
        meta=dict(element_id=e['element_id'],source_sha256=e['source_sha256'],sha256=digest(body),reason=reason)
        rendered[e['element_id']]='<!-- paper-figure '+json.dumps(meta,ensure_ascii=False,separators=(',',':'))+' -->\n'+body+'<!-- /paper-figure -->\n'
    # Existing blocks keep their positions; surrounding human prose is untouched.
    text=PATTERN.sub(lambda match: rendered[json.loads(match[1])['element_id']],text)
    added=[rendered[e['element_id']] for e in figures if e['element_id'] not in previous]
    if added:
        section=('' if previous else '## Figures\n\n')+'\n'.join(added)+'\n'
        point=text.find('## Ingest log\n')
        if point<0: text=text.rstrip()+'\n\n'+section
        else: text=text[:point]+section+text[point:]
    verify(text,manifest,page,image_root=image_root,require_local=False)
    return text


def verify(text,manifest,page,*,image_root=None,require_local=True):
    import final_products as fp
    m=fp.verify(manifest);_,paths=pa.verify_local(manifest)
    image_root=absolute(image_root or absolute(manifest).parent)
    index={e['element_id']:e for e in m['elements']}
    values=blocks(text)
    required={e['element_id'] for e in m['elements'] if e['kind']=='figure' and role(e,m)=='manuscript'}
    present={meta['element_id'] for meta,_ in values}
    require(required<=present,'manuscript-figure-embed-missing')
    for meta,body in values:
        e=index.get(meta['element_id'])
        require(e and e['kind']=='figure' and e['source_sha256']==meta['source_sha256'],'figure-source-binding')
        require(role(e,m)=='manuscript' or (role(e,m)=='supplement' and meta.get('reason','').strip()),'supplement-reason-required')
        links=re.findall(r'!\[(?:\\.|[^\]])*\]\(([^\n)]+)\)',body)
        fragments=e['evidence'].get('body_fragments',[])
        require(len(links)==len(fragments),'figure-fragment-count')
        for link,fragment in zip(links,fragments):
            require(not re.match(r'[a-zA-Z][a-zA-Z0-9+.-]*:',link) and not link.startswith('/'),'local-relative-figure-required')
            target=(absolute(page).parent/unquote(link)).resolve()
            require(target==(image_root/fragment['crop']).resolve(),'figure-crop-binding')
            require(pa.sha(paths[fragment['crop']])==fragment['crop_sha256'],'figure-crop-hash')
            if require_local: require(target.is_file() and pa.sha(target)==fragment['crop_sha256'],'figure-image-missing-or-changed')
    return len(values)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command',choices=('render','verify'))
    parser.add_argument('--manifest',required=True);parser.add_argument('--page',required=True)
    parser.add_argument('--output');parser.add_argument('--supplement',action='append',default=[],metavar='ELEMENT_ID=REASON')
    args=parser.parse_args();page=absolute(args.page)
    try:
        if args.command=='render':
            require(args.output is not None,'new-output-required')
            supplements=dict(item.split('=',1) for item in args.supplement)
            value=render(page.read_text(),args.manifest,page,supplements=supplements)
            # Candidate only; the caller owns guarded application and page receipts.
            with absolute(args.output).open('x') as out: out.write(value)
        else: print(json.dumps(dict(figures=verify(page.read_text(),args.manifest,page))))
        return 0
    except (ValueError,OSError,KeyError,TypeError) as exc:
        print(str(exc));return 2

if __name__=='__main__': raise SystemExit(main())
