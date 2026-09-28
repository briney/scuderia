"""Retain originals, expose manuscript text, never enumerate scientific elements."""
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import shutil
import xml.etree.ElementTree as ET
from . import workflow as w


class TextHTML(HTMLParser):
    def __init__(self):
        super().__init__(); self.parts=[]; self.hidden=0
    def handle_starttag(self,tag,attrs):
        if tag in ('script','style'): self.hidden+=1
        if tag in ('p','div','br','h1','h2','h3','tr'): self.parts.append('\n')
    def handle_endtag(self,tag):
        if tag in ('script','style'): self.hidden=max(0,self.hidden-1)
    def handle_data(self,data):
        if not self.hidden: self.parts.append(data)


def text_pages(path):
    if path.suffix=='.pdf':
        import pymupdf
        with pymupdf.open(path) as pdf:
            w.require(pdf.is_pdf and not pdf.needs_pass and len(pdf)>0,'unreadable-manuscript-pdf')
            return [page.get_text(sort=True) for page in pdf]
    raw=path.read_text()
    if path.suffix in ('.xml','.nxml'):
        root=ET.fromstring(raw); return ['\n'.join(root.itertext())]
    if path.suffix in ('.html','.htm'):
        parser=TextHTML(); parser.feed(raw); return [''.join(parser.parts)]
    w.require(path.suffix in ('.txt','.md'),'unsupported-manuscript-format')
    return [raw]


def verify_sources(job,work):
    for row in job.get('sources',[]):
        w.require(w.sha(work/row['key'])==row['sha256'],'corrupt-source:'+row['source_id'])
        for page in row.get('text',[]):
            w.require(w.sha(work/page['key'])==page['sha256'],'corrupt-retained-text')


def index(job):
    return [{k:v for k,v in row.items() if k not in ('key','text')} for row in job['sources']]


def prepare(job_id,inputs=None,*,runtime_root):
    settings=w.config(runtime_root); work=w.job_path(job_id,runtime_root)
    with w.locked(work):
        job=w.load_job(job_id,runtime_root)
        if job.get('sources'):
            w.require(inputs is None,'sources-already-bound; start a separately reconciled job for different source bytes')
            verify_sources(job,work)
            return w.result(job,runtime_root,sources=index(job))
        if inputs is None and job.get('prior_receipt'):
            from . import archive
            restored=archive.open_sources(Path(job['prior_receipt']),work/'prior',transport=settings.get('archive'))
            for field in ('doi','pmid','version'):
                before=restored['identity'].get(field); after=job['identity'].get(field)
                w.require(not before or not after or before==after,'archive-identity-reconciliation-required:'+field)
            if not job['identity'].get('version'): job['identity']['version']=restored['identity'].get('version')
            inputs=restored['inputs']; job['history']=restored['history']
        if not inputs:
            job.update(status='needs-input',next_action='Acquire the manuscript with the existing full-text acquisition helper, then supply retained inputs.',blocking_reason='essential-source-unavailable')
            w.store_job(job,runtime_root); return w.result(job,runtime_root)
        w.require(isinstance(inputs,list) and len(inputs)<=1000,'invalid-source-inputs')
        w.require(sum(row.get('role')=='manuscript' for row in inputs)==1,'select-one-manuscript; retain alternatives as supplements')
        # Validate all essential input identity before retaining anything.
        for row in inputs:
            w.require(row.get('role') in ('manuscript','body','supplement'),'invalid-source-role')
            if row['role'] in ('manuscript','body'):
                identity=row.get('identity',{}); supplied=False
                for field in ('doi','pmid','version'):
                    if identity.get(field):
                        supplied=True; w.require(identity[field]==job['identity'].get(field),'source-identity-mismatch:'+field)
                w.require(supplied and str(row.get('basis','')).strip(),'source-identity-basis-required')
        retained=[]; seen=set()
        for row in inputs:
            source=w.absolute(row['path'])
            if not source.is_file():
                w.require(row['role']=='supplement','essential-source-unavailable')
                job['warnings'].append('Supplement retention gap: '+source.name); continue
            h=w.sha(source); sid='s-'+h[:24]
            w.require(sid not in seen,'duplicate-source-bytes; retain aliases as metadata')
            seen.add(sid)
            suffix=source.suffix.lower(); suffix=suffix if re.fullmatch(r'\.[a-z0-9]{1,10}',suffix) else '.bin'
            key='sources/'+h+suffix; target=work/key; target.parent.mkdir(exist_ok=True)
            if not target.exists(): shutil.copyfile(source,target)
            w.require(w.sha(target)==h,'source-changed-during-retention')
            item=dict(source_id=sid,role=row['role'],filename=source.name,key=key,sha256=h,size=target.stat().st_size,
                identity=row.get('identity'),basis=row.get('basis'),source_url=row.get('source_url'))
            if row['role'] in ('manuscript','body'):
                pages=text_pages(target); selected=row.get('pages',list(range(1,len(pages)+1)))
                w.require(selected and all(type(n) is int and 1<=n<=len(pages) for n in selected) and selected==sorted(set(selected)),'invalid-manuscript-boundaries')
                item.update(pages=len(pages),selected_pages=selected,text=[],deficient_pages=[])
                for number in selected:
                    text=pages[number-1]; tk='text/'+sid+'-'+str(number)+'.txt'; (work/'text').mkdir(exist_ok=True)
                    (work/tk).write_text(text)
                    item['text'].append(dict(page=number,key=tk,sha256=w.sha(work/tk),characters=len(text)))
                    if len(text.strip())<30:item['deficient_pages'].append(number)
                if item['deficient_pages']:job['warnings'].append('Specific manuscript evidence needs inspection: '+sid+' pages '+str(item['deficient_pages']))
            retained.append(item)
        job.update(sources=retained,status='working',blocking_reason=None,next_action='Read every manuscript location; use bounded inspection only where essential evidence is deficient.')
        w.store_job(job,runtime_root)
        return w.result(job,runtime_root,sources=index(job))


def select(job,locations):
    w.require(isinstance(locations,list) and 0<len(locations)<=8,'explicit-bounded-locations-required')
    selected=[]
    for location in locations:
        w.require(set(location)<= {'source_id','page','start_char','max_chars'},'unknown-location-field')
        row=next((x for x in job['sources'] if x['source_id']==location.get('source_id')),None)
        w.require(row is not None and row['role'] in ('manuscript','body'),'out-of-scope-source')
        page=location.get('page'); w.require(type(page) is int and page in row['selected_pages'],'out-of-scope-page')
        selected.append((row,next(x for x in row['text'] if x['page']==page),location))
    return selected


def read(job_id,locations,*,runtime_root,question=None):
    if question is not None:return inspect(job_id,locations,question,runtime_root=runtime_root)
    work=w.job_path(job_id,runtime_root)
    with w.locked(work):
        job=w.load_job(job_id,runtime_root); selected=select(job,locations); verify_sources(job,work); output=[]
        for row,page,location in selected:
            text=(work/page['key']).read_text(); start=location.get('start_char',0); limit=location.get('max_chars',16000)
            w.require(type(start) is int and 0<=start<=len(text) and type(limit) is int and 1<=limit<=32000,'invalid-text-window')
            end=min(start+limit,len(text)); token=row['source_id']+':'+str(page['page'])
            output.append(dict(source_id=row['source_id'],page=page['page'],text=text[start:end],start_char=start,
                partial=end<len(text),next_start=end if end<len(text) else None,characters=len(text),deficient=page['page'] in row['deficient_pages']))
            job.setdefault('reads',{}).setdefault(token,[]).append([start,end])
        w.store_job(job,runtime_root)
        return w.result(job,runtime_root,locations=output)
