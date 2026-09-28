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


def hold_live_edit(job,work):
    """Capture bytes once; an opaque token binds a subsequent reviewed reconciliation."""
    import hashlib
    page=Path(job['page']); raw=page.read_bytes() if page.exists() else None
    current=hashlib.sha256(raw).hexdigest() if raw is not None else None
    allowed={job.get('apply_guard_sha256',job['original_sha256'])}
    for name in ('pending-page.md','page.md'):
        archived=work/'archives'/str(job['revision'])/name
        if archived.exists():allowed.add(sha(archived))
    if current in allowed:return False
    snapshot=job.get('live_snapshot')
    if not snapshot or snapshot['sha256']!=current:
        token=uuid.uuid4().hex; path=work/'live'/ (token+'.md'); path.parent.mkdir(exist_ok=True)
        path.write_bytes(raw or b'')
        snapshot=dict(token=token,path=str(path),sha256=current)
        job['live_snapshot']=snapshot
    job.update(status='held',blocking_reason='concurrent-page-edit',
        next_action='Read artifacts.live_snapshot.path, reconcile the candidate with that live page, then stage with its opaque token as base_revision.',
        artifacts={**job['artifacts'],'live_snapshot':snapshot})
    return True


def status(job_id,*,runtime_root):
    work=job_path(job_id,runtime_root)
    with locked(work):
        job=load_job(job_id,runtime_root)
        if job['status']!='complete' and hold_live_edit(job,work):store_job(job,runtime_root)
        return result(job,runtime_root)


def start(page,*,runtime_root,identity=None):
    settings=config(runtime_root); page=absolute(page); instance=absolute(settings['instance'])
    require(page.parent==instance/'papers' and page.suffix=='.md','paper-path-outside-configured-instance')
    original_bytes=page.read_bytes() if page.exists() else None
    original=original_bytes.decode('utf-8') if original_bytes is not None else None
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
                require(all(prior['identity'].get(k)==v for k,v in bound.items() if v is not None),'active-job-identity-conflict')
                return result(prior,runtime_root)
        job_id=uuid.uuid4().hex; work=job_path(job_id,runtime_root); work.mkdir(parents=True,mode=0o700)
        if original is not None: (work/'original.md').write_bytes(original_bytes)
        job=dict(job_id=job_id,scope='manuscript-to-page',page=str(page),identity=bound,
            original_sha256=sha(work/'original.md') if original is not None else None,status='working',
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
    useful=False
    for source in job.get('sources',[]):
        if source['role'] not in ('manuscript','body'): continue
        for page in source['text']:
            token=source['source_id']+':'+str(page['page'])
            if page['page'] in source.get('deficient_pages',[]) and token in job.get('transcribed',[]):
                useful=True
                continue
            ranges=job.get('reads',{}).get(token,[])
            if not ranges:return False
            end=0
            for left,right in sorted(ranges):
                if left>end:return False
                end=max(end,right)
            if end<page['characters']:return False
            useful=useful or page['characters']>=30
    # Deficient peripheral pages remain visible warnings, not compulsory model calls.
    # An entirely unreadable manuscript still needs actual inspection or faithful body text.
    return useful


def stage(job_id,markdown,review_note,*,runtime_root,base_revision=None):
    from .sources import verify_sources
    import difflib
    work=job_path(job_id,runtime_root)
    with locked(work):
        job=load_job(job_id,runtime_root)
        require(job['status']!='complete','job-already-complete')
        base=Path(job.get('base_snapshot',work/'original.md'))
        if base_revision is not None:
            snapshot=job.get('live_snapshot',{})
            require(base_revision==snapshot.get('token') and snapshot,'unknown-live-snapshot')
            base=Path(snapshot['path'])
            require((sha(job['page']) if Path(job['page']).exists() else None)==snapshot['sha256'],'stale-live-snapshot; check status again')
            require(snapshot['sha256'] is None or sha(base)==snapshot['sha256'],'corrupt-live-snapshot')
            job['apply_guard_sha256']=snapshot['sha256']
            job['base_snapshot']=str(base)
            job.pop('applied_revision',None)
        elif hold_live_edit(job,work):
            store_job(job,runtime_root); return result(job,runtime_root)
        elif job.get('applied_revision'):
            pending=work/'archives'/str(job['applied_revision'])/'pending-page.md'
            require(sha(job['page'])==sha(pending),'concurrent-page-edit')
            base=pending; job['base_snapshot']=str(base)
            job['apply_guard_sha256']=sha(pending)
            job.pop('applied_revision')
        require(isinstance(markdown,str) and 0<len(markdown)<=2_000_000,'invalid-draft')
        require(isinstance(review_note,str) and 10<=len(review_note.strip())<=32000,'focused-source-review-note-required')
        require(manuscript_read(job),'read-entire-manuscript-before-staging')
        verify_sources(job,work)
        from . import citations
        annotated=markdown
        markdown,evidence=citations.extract(markdown,job,work)
        for warning in evidence['warnings']:
            if warning not in job['warnings']:job['warnings'].append(warning)
        fm=page_metadata(markdown)
        for field in ('slug','title','doi','pmid'):
            require(fm.get(field)==job['identity'].get(field),'candidate-identity-mismatch:'+field)
        require(fm.get('kind')=='paper','paper-kind-required')
        for snapshot in {work/'original.md',base}:
            if not snapshot.exists() or not snapshot.read_bytes():continue
            original_meta=page_metadata(snapshot.read_text())
            require(set(original_meta.get('cited_by') or [])<=set(fm.get('cited_by') or []),'original-citing-edges-missing')
            for field in ('stub_source','ingest_attempts'):
                require(field not in original_meta or fm.get(field)==original_meta[field],'original-provenance-changed:'+field)
        require(re.search(r'^# '+re.escape(fm['title'])+r'\s*$',markdown,re.M),'paper-title-heading-required')
        require(not re.search(r'!\[|!\[\[|source-packages/|<img\b|portable-article-register|qualification-register',markdown,re.I),'article-payload-or-register-in-page')
        # Optional source locators are accepted only when they identify retained evidence.
        for sid,page in re.findall(r'\[source:([^:\]]+):(\d+)\]',markdown+'\n'+review_note):
            require(any(s['source_id']==sid and int(page) in s.get('selected_pages',[]) for s in job['sources']),'unresolved-source-reference')
        holds=[line.strip()[5:].strip() for line in review_note.splitlines() if line.strip().startswith('HOLD:')]
        drafts=work/'drafts'; drafts.mkdir(exist_ok=True)
        revision=max([job['revision']]+[int(p.name) for p in drafts.iterdir() if p.name.isdecimal()])+1
        draft=Path(tempfile.mkdtemp(prefix='.stage-',dir=drafts))
        receipt_name=Path(job['page']).stem+'.article-'+job_id+'-'+str(revision)+'.json'
        # Keep the queue marker until deterministic integration succeeds.
        if re.search(r'^needs-ingest:',markdown,re.M): markdown=re.sub(r'^needs-ingest:.*$','needs-ingest: true',markdown,count=1,flags=re.M)
        else: markdown=markdown.replace('---\n','---\nneeds-ingest: true\n',1)
        markdown=re.sub(r'^Article archive: .*\n?','',markdown,flags=re.M).rstrip()+'\n\nArticle archive: '+receipt_name+'\n'
        (draft/'page.md').write_text(markdown); (draft/'review.txt').write_text(review_note)
        (draft/'annotated-page.md').write_text(annotated)
        evidence['draft_sha256']=sha(draft/'page.md')
        save(draft/'citations.json',evidence)
        original=base.read_text() if base.exists() else ''
        diff=''.join(difflib.unified_diff(original.splitlines(True),markdown.splitlines(True),fromfile='original',tofile='candidate'))
        (draft/'page.diff').write_text(diff)
        meta=dict(revision=revision,page_sha256=sha(draft/'page.md'),review_sha256=sha(draft/'review.txt'),
            citation_products={name:sha(draft/name) for name in ('annotated-page.md','citations.json')},
            receipt_name=receipt_name,material_issues=holds,source_hashes=[s['sha256'] for s in job['sources']],
            base_snapshot=str(base),base_sha256=job.get('apply_guard_sha256',job['original_sha256']))
        save(draft/'revision.json',meta)
        os.rename(draft,drafts/str(revision)); draft=drafts/str(revision)
        job.update(revision=revision,status='held' if holds else 'ready',blocking_reason='material-review-issues' if holds else None,
            next_action='Correct, qualify, or omit held claims and stage a new revision.' if holds else 'Publish this reviewed revision; archive verification precedes guarded page application.',
            artifacts=dict(revision=revision,draft=str(draft/'page.md'),diff=str(draft/'page.diff'),review=str(draft/'review.txt'),citations=str(draft/'citations.json'),annotated_draft=str(draft/'annotated-page.md')))
        store_job(job,runtime_root); return result(job,runtime_root)


def integration_check(job,settings):
    """Existing page/identity checks plus author edges and propagation read-back."""
    import importlib.util
    import subprocess
    import sys
    import yaml
    helper=Path(__file__).resolve().parents[2]/'skills/paper-ingest/scripts/verify_ingest.py'
    spec=importlib.util.spec_from_file_location('_manuscript_verify_ingest',helper)
    verifier=importlib.util.module_from_spec(spec); spec.loader.exec_module(verifier)
    page=Path(job['page']); text=page.read_text(); fm=page_metadata(text); final=dict(fm,**{'needs-ingest':False})
    issues=verifier.filled_contract_checks(final,text,page.stem)
    argv=[sys.executable,'-B',str(helper),page.stem,'--instance',settings['instance']]
    # This subprocess checks canonical identity and forward graph links. No inference.
    checked=subprocess.run(argv,capture_output=True,text=True,timeout=180)
    if checked.returncode:issues.append(checked.stdout[-12000:] or 'page-identity-or-graph-check-failed')
    instance=Path(settings['instance']); ledger_path=instance/'people/_ledger.yaml'
    ledger=yaml.safe_load(ledger_path.read_text()) if ledger_path.exists() else {}
    entries=ledger.get('authors',[]) if isinstance(ledger,dict) else ledger if isinstance(ledger,list) else []
    # The convention uses entries; handle older authors-shaped ledgers read-only.
    if isinstance(ledger,dict):entries=ledger.get('entries',entries)
    target='papers/'+page.stem
    for author in fm.get('authors',[]):
        person=instance/(author+'.md')
        if person.exists():
            meta=page_metadata(person.read_text()); edges=meta.get('author_on',[])
        else:
            entry=next((e for e in entries if isinstance(e,dict) and e.get('slug')==author.removeprefix('people/')),None)
            edges=entry.get('citations',[]) if entry else []
        if target not in edges:issues.append('author-edge-missing:'+author)
    inbox=instance/'docs/rem-cycle/inbox.yaml'
    events=yaml.safe_load(inbox.read_text()) if inbox.exists() else {}
    if not isinstance(events,dict) or not any(e.get('page')==target and e.get('event') in ('ingest','stub-filled') for e in events.get('items',[]) if isinstance(e,dict)):
        issues.append('propagation-event-missing')
    if not re.search(r'bibliograph|[Dd]eferred stubs',text,re.I):issues.append('Record source-backed bibliography decisions in the Ingest log.')
    return issues


def apply_bytes(path,raw,expected_hash):
    """Compare immediately before atomic replacement; never overwrite a stale page."""
    path=absolute(path)
    require((sha(path) if path.exists() else None)==expected_hash,'concurrent-page-edit')
    fd,name=tempfile.mkstemp(dir=path.parent,prefix='.paper-')
    try:
        with os.fdopen(fd,'wb') as f:f.write(raw); f.flush(); os.fsync(f.fileno())
        require((sha(path) if path.exists() else None)==expected_hash,'concurrent-page-edit')
        os.replace(name,path)
    finally:
        if os.path.exists(name):os.unlink(name)


def publish(job_id,revision,*,runtime_root):
    from . import archive
    work=job_path(job_id,runtime_root); settings=config(runtime_root)
    with locked(work):
        job=load_job(job_id,runtime_root)
        require(type(revision) is int and revision==job['revision'],'publish-current-reviewed-revision')
        if job.get('applied_revision'):require(job['applied_revision']==revision,'different-revision-already-applied')
        manifest=archive.build(job_id,revision,runtime_root=runtime_root); m=archive.verify(manifest)
        page=absolute(job['page']); root=manifest.parent; pending=root/'pending-page.md'; final=root/'page.md'
        if job['status']=='complete':
            require(sha(page)==sha(final),'completed-page-changed')
            return result(job,runtime_root)
        publication_path=root/'publication.json'
        try:
            if publication_path.exists():pub=archive.publication_check(manifest,json.loads(publication_path.read_text()))
            else:
                pub=archive.publish(manifest,destination=settings['archive']); save(publication_path,pub)
        except (ValueError,OSError,KeyError) as exc:
            job.update(status='publication-pending',blocking_reason=str(exc),next_action='Retry publish after archive availability/configuration is corrected; no inference will repeat.')
            store_job(job,runtime_root); return result(job,runtime_root)
        current=sha(page) if page.exists() else None
        if current not in (job.get('apply_guard_sha256',job['original_sha256']),sha(pending),sha(final)):
            hold_live_edit(job,work)
            store_job(job,runtime_root); return result(job,runtime_root)
        receipt=page.parent/m['receipt_name']
        if receipt.exists():require(json.loads(receipt.read_text())==pub,'existing-publication-receipt-changed')
        else:save(receipt,pub)
        if current==job.get('apply_guard_sha256',job['original_sha256']):apply_bytes(page,pending.read_bytes(),current)
        job['applied_revision']=revision; job.update(status='integration-pending',next_action='Complete author, graph, bibliography, and propagation obligations, then publish again.',blocking_reason=None)
        store_job(job,runtime_root)
        try: issues=integration_check(job,settings)
        except Exception as exc:issues=['integration-check-unavailable:'+type(exc).__name__]
        if issues:
            job.update(blocking_reason='integration-obligations',artifacts={**job['artifacts'],'integration_obligations':issues,'manifest':str(manifest),'receipt':str(receipt)})
        else:
            current=sha(page)
            require(current in (sha(pending),sha(final)),'concurrent-page-edit')
            if current!=sha(final):apply_bytes(page,final.read_bytes(),current)
            job.update(status='complete',blocking_reason=None,next_action='Ingestion is complete; commit the reviewed owned page, receipt, and integration edits using git-ops.',
                artifacts={**job['artifacts'],'manifest':str(manifest),'receipt':str(receipt),'integration_obligations':[]})
        store_job(job,runtime_root); return result(job,runtime_root)
