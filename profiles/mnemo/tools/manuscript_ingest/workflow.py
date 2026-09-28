"""Durable ordinary jobs. Configuration is operator-owned, never tool arguments."""
import json
import os
from pathlib import Path
import re
import tempfile
import uuid
from article_archive_compat.article_runtime import absolute, outside_instance, require, sha, digest, locked


def save(path, value):
    path=absolute(path); path.parent.mkdir(parents=True,exist_ok=True)
    fd, name=tempfile.mkstemp(dir=path.parent,prefix='.write-')
    try:
        with os.fdopen(fd,'w') as f:
            json.dump(value,f,ensure_ascii=False,allow_nan=False,indent=2); f.write('\n'); f.flush(); os.fsync(f.fileno())
        os.replace(name,path)
        fd=os.open(path.parent,os.O_RDONLY)
        try: os.fsync(fd)
        finally: os.close(fd)
    finally:
        if os.path.exists(name): os.unlink(name)


def config(runtime_root):
    root=outside_instance(runtime_root)
    value=json.loads((root/'config.json').read_text())
    instance=absolute(value['instance'])
    require(not root.is_relative_to(instance) and not instance.is_relative_to(root),'runtime-must-be-outside-instance')
    return value


def page_metadata(text):
    import yaml
    match=re.match(r'\A---\s*\n(.*?)\n---\s*\n',text,re.S)
    require(match is not None,'paper-frontmatter-required')
    value=yaml.safe_load(match[1]); require(isinstance(value,dict),'paper-frontmatter-mapping-required')
    return value


def job_path(job_id,runtime_root):
    require(isinstance(job_id,str) and re.fullmatch('[0-9a-f]{32}',job_id),'invalid-job-id')
    return absolute(runtime_root)/'jobs'/job_id


def load_job(job_id,runtime_root):
    config(runtime_root)
    job=json.loads((job_path(job_id,runtime_root)/'job.json').read_text())
    require(job['job_id']==job_id and job['scope']=='manuscript-to-page','job-scope-mismatch')
    return job


def store_job(job,runtime_root):
    save(job_path(job['job_id'],runtime_root)/'job.json',job)


def result(job,runtime_root,**artifacts):
    return dict(job_id=job['job_id'],status=job['status'],next_action=job['next_action'],
        artifacts=dict(work=str(job_path(job['job_id'],runtime_root)),**job.get('artifacts',{}),**artifacts),
        warnings=job.get('warnings',[]),blocking_reason=job.get('blocking_reason'))


def status(job_id,*,runtime_root):
    return result(load_job(job_id,runtime_root),runtime_root)


def start(page,*,runtime_root,identity=None):
    settings=config(runtime_root); page=absolute(page); instance=absolute(settings['instance'])
    require(page.parent==instance/'papers' and page.suffix=='.md','paper-path-outside-configured-instance')
    original=page.read_text() if page.exists() else None
    fm=page_metadata(original) if original else {}
    bound={k:fm.get(k) for k in ('slug','title','doi','pmid','version')}; bound['slug']=page.stem
    for k,v in (identity or {}).items():
        require(k in bound,'unknown-identity-field')
        require(not bound.get(k) or bound[k]==v,'article-identity-conflict:'+k)
        bound[k]=v
    require(bound.get('title') and (bound.get('doi') or bound.get('pmid')),'resolved-article-identity-required')
    with locked(runtime_root):
        index_path=absolute(runtime_root)/'active.json'
        index=json.loads(index_path.read_text()) if index_path.exists() else {}
        if str(page) in index:
            prior=load_job(index[str(page)],runtime_root)
            if prior['status']!='complete':
                require(prior['identity']==bound,'active-job-identity-conflict')
                return result(prior,runtime_root)
        job_id=uuid.uuid4().hex; work=job_path(job_id,runtime_root); work.mkdir(parents=True,mode=0o700)
        if original is not None: (work/'original.md').write_text(original)
        job=dict(job_id=job_id,scope='manuscript-to-page',page=str(page),identity=bound,
            original_sha256=sha(page) if original is not None else None,status='working',
            next_action='Retain manuscript and supplementary inputs with sources, or reuse the existing article archive.',
            revision=0,warnings=[],blocking_reason=None,artifacts={},
            authorization={'max_requests':settings.get('inspection_budget',0)})
        pointer=re.search(r'^Article archive: (.+)$',original or '',re.M)
        if pointer:
            receipt=absolute(page.parent/pointer[1]); require(receipt.is_relative_to(instance),'archive-pointer-outside-instance')
            job['prior_receipt']=str(receipt)
        store_job(job,runtime_root); index[str(page)]=job_id; save(index_path,index)
        return result(job,runtime_root)


def manuscript_read(job):
    """Delivery coverage only, never a certificate of scientific understanding."""
    for source in job.get('sources',[]):
        if source['role']!='manuscript': continue
        for page in source['text']:
            token=source['source_id']+':'+str(page['page'])
            if page['page'] in source['deficient_pages']:
                if token not in job.get('inspected',[]): return False
                continue
            end=0
            for left,right in sorted(job.get('reads',{}).get(token,[])):
                if left>end:return False
                end=max(end,right)
            if end<page['characters']:return False
    return bool(job.get('sources'))


def stage(job_id,markdown,review_note,*,runtime_root):
    from .sources import verify_sources
    import difflib
    work=job_path(job_id,runtime_root)
    with locked(work):
        job=load_job(job_id,runtime_root)
        require(job['status'] not in ('complete','integration-pending'),'job-already-applied')
        require(isinstance(markdown,str) and 0<len(markdown)<=2_000_000,'invalid-draft')
        require(isinstance(review_note,str) and 10<=len(review_note.strip())<=32000,'focused-source-review-note-required')
        require(manuscript_read(job),'read-entire-manuscript-before-staging')
        verify_sources(job,work)
        fm=page_metadata(markdown)
        for field in ('slug','title','doi','pmid'):
            require(fm.get(field)==job['identity'].get(field),'candidate-identity-mismatch:'+field)
        require(fm.get('kind')=='paper','paper-kind-required')
        require(re.search(r'^# '+re.escape(fm['title'])+r'\s*$',markdown,re.M),'paper-title-heading-required')
        require(not re.search(r'!\[|!\[\[|source-packages/|<img\b|portable-article-register|qualification-register',markdown,re.I),'article-payload-or-register-in-page')
        # Optional source locators are accepted only when they identify retained evidence.
        for sid,page in re.findall(r'\[source:(s-[a-f0-9]+):(\d+)\]',markdown+'\n'+review_note):
            require(any(s['source_id']==sid and int(page) in s.get('selected_pages',[]) for s in job['sources']),'unresolved-source-reference')
        holds=[line.strip()[5:].strip() for line in review_note.splitlines() if line.strip().startswith('HOLD:')]
        revision=job['revision']+1; draft=work/'drafts'/str(revision); draft.mkdir(parents=True)
        receipt_name=Path(job['page']).stem+'.article-'+job_id+'-'+str(revision)+'.json'
        # Keep the queue marker until deterministic integration succeeds.
        if re.search(r'^needs-ingest:',markdown,re.M): markdown=re.sub(r'^needs-ingest:.*$','needs-ingest: true',markdown,count=1,flags=re.M)
        else: markdown=markdown.replace('---\n','---\nneeds-ingest: true\n',1)
        markdown=re.sub(r'^Article archive: .*\n?','',markdown,flags=re.M).rstrip()+'\n\nArticle archive: '+receipt_name+'\n'
        (draft/'page.md').write_text(markdown); (draft/'review.txt').write_text(review_note)
        original=(work/'original.md').read_text() if (work/'original.md').exists() else ''
        diff=''.join(difflib.unified_diff(original.splitlines(True),markdown.splitlines(True),fromfile='original',tofile='candidate'))
        (draft/'page.diff').write_text(diff)
        meta=dict(revision=revision,page_sha256=sha(draft/'page.md'),review_sha256=sha(draft/'review.txt'),
            receipt_name=receipt_name,material_issues=holds,source_hashes=[s['sha256'] for s in job['sources']])
        save(draft/'revision.json',meta)
        job.update(revision=revision,status='held' if holds else 'ready',blocking_reason='material-review-issues' if holds else None,
            next_action='Correct, qualify, or omit held claims and stage a new revision.' if holds else 'Publish this reviewed revision; archive verification precedes guarded page application.',
            artifacts=dict(revision=revision,draft=str(draft/'page.md'),diff=str(draft/'page.diff'),review=str(draft/'review.txt')))
        store_job(job,runtime_root); return result(job,runtime_root)
