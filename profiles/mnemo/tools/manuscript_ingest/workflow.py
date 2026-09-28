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
