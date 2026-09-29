"""Durable ordinary jobs. Configuration is operator-owned, never tool arguments."""
import json
import os
from pathlib import Path
import re
import tempfile
import uuid
import time
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


def identity_value(field,value):
    if field=='pmid' and (type(value) is int or isinstance(value,str)):
        return str(value).strip()
    if field=='version' and isinstance(value,str):
        return re.sub(r'[\s_-]+',' ',value.strip().casefold())
    return value


def same_identity(field,left,right):
    return identity_value(field,left)==identity_value(field,right)


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


def mark_time(job,event):
    job.setdefault('timings',{}).setdefault(event,time.time())


def result(job,runtime_root,**artifacts):
    if job.get('sources'):
        artifacts['source_retention']=dict(
            manuscript_formats=sorted({Path(s['key']).suffix for s in job['sources'] if s['role'] in ('manuscript','body')}),
            supplementary_files=sum(s['role']=='supplement' for s in job['sources']),
            attachment_completeness='not-certified',
            gaps=[warning for warning in job.get('warnings',[]) if 'retention gap' in warning.lower()])
    return dict(job_id=job['job_id'],status=job['status'],next_action=job['next_action'],
        artifacts=dict(work=str(job_path(job['job_id'],runtime_root)),**job.get('artifacts',{}),**artifacts),
        warnings=job.get('warnings',[]),blocking_reason=job.get('blocking_reason'))


def hold_live_edit(job,work,*,capture=False):
    """Capture bytes once; an opaque token binds a subsequent reviewed reconciliation."""
    import hashlib
    page=Path(job['page']); raw=page.read_bytes() if page.exists() else None
    current=hashlib.sha256(raw).hexdigest() if raw is not None else None
    allowed={job.get('apply_guard_sha256',job['original_sha256'])}
    for name in ('pending-page.md','page.md'):
        archived=work/'archives'/str(job['revision'])/name
        if archived.exists():allowed.add(sha(archived))
    changed=current not in allowed
    if not changed and not capture:return False
    snapshot=job.get('live_snapshot')
    if not snapshot or snapshot['sha256']!=current:
        token=uuid.uuid4().hex; path=work/'live'/ (token+'.md'); path.parent.mkdir(exist_ok=True)
        path.write_bytes(raw or b'')
        snapshot=dict(token=token,path=str(path),sha256=current)
        job['live_snapshot']=snapshot
    job['artifacts']={**job['artifacts'],'live_snapshot':snapshot}
    if not changed:return False
    job.update(status='held',blocking_reason='concurrent-page-edit',
        next_action='Read artifacts.live_snapshot.path, reconcile the candidate with that live page, then stage with its opaque token as base_revision.',
        artifacts={**job['artifacts'],'live_snapshot':snapshot})
    return True


def status(job_id,*,runtime_root):
    work=job_path(job_id,runtime_root)
    with locked(work):
        job=load_job(job_id,runtime_root)
        if job['status']=='complete':job.setdefault('published_revision',job['revision'])
        hold_live_edit(job,work,capture=bool(job.get('published_revision')))
        store_job(job,runtime_root)
        return result(job,runtime_root)


def start(page,*,runtime_root,identity=None):
    settings=config(runtime_root); page=absolute(page); instance=absolute(settings['instance'])
    require(page.parent==instance/'papers' and page.suffix=='.md','paper-path-outside-configured-instance')
    original_bytes=page.read_bytes() if page.exists() else None
    original=original_bytes.decode('utf-8') if original_bytes is not None else None
    fm=page_metadata(original) if original else {}
    bound={k:fm.get(k) for k in ('slug','title','doi','pmid','version')}; bound['slug']=page.stem
    if bound.get('pmid') is not None:bound['pmid']=identity_value('pmid',bound['pmid'])
    for k,v in (identity or {}).items():
        require(k in bound,'unknown-identity-field')
        require(k!='slug' or v==page.stem,'article-identity-conflict:slug')
        bound[k]=identity_value(k,v) if k=='pmid' else v
    require(bound.get('title') and (bound.get('doi') or bound.get('pmid')),'resolved-article-identity-required')
    with locked(runtime_root):
        index_path=absolute(runtime_root)/'active.json'
        index=json.loads(index_path.read_text()) if index_path.exists() else {}
        if str(page) in index:
            prior=load_job(index[str(page)],runtime_root)
            if prior['status']!='complete':
                require(all(same_identity(k,prior['identity'].get(k),v) for k,v in bound.items() if v is not None),'active-job-identity-conflict')
                return result(prior,runtime_root)
        job_id=uuid.uuid4().hex; work=job_path(job_id,runtime_root); work.mkdir(parents=True,mode=0o700)
        if original is not None: (work/'original.md').write_bytes(original_bytes)
        job=dict(job_id=job_id,scope='manuscript-to-page',page=str(page),identity=bound,
            original_sha256=sha(work/'original.md') if original is not None else None,status='working',
            next_action='Retain manuscript and supplementary inputs with sources, or reuse the existing article archive.',
            revision=0,warnings=[],blocking_reason=None,artifacts={},
            authorization={'max_requests':settings.get('inspection_budget',0)})
        mark_time(job,'started_at')
        pointer=re.search(r'^Article archive: (.+)$',original or '',re.M)
        if pointer:
            if pointer[1].startswith('r2://'):
                from .archive import receipt_key
                receipt_key(pointer[1],settings.get('archive'))
                job['prior_receipt']=pointer[1]
            else:
                raw=page.parent/pointer[1]
                require(not any(p.is_symlink() for p in (raw,*raw.parents)),'archive-pointer-symlink')
                receipt=absolute(Path(os.path.normpath(raw))); require(receipt.is_relative_to(instance),'archive-pointer-outside-instance')
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


def stage(job_id,markdown,review_note,*,runtime_root,base_revision=None,amend_revision=None):
    from .sources import verify_sources
    import difflib
    work=job_path(job_id,runtime_root)
    with locked(work):
        job=load_job(job_id,runtime_root)
        if job['status']=='complete':job.setdefault('published_revision',job['revision'])
        published=job.get('published_revision')
        if amend_revision is not None:
            require(type(amend_revision) is int and amend_revision==published==job['revision'],'amend-current-published-revision')
            require(base_revision is not None,'amend-live-snapshot-required; check status and reconcile first')
        else:
            require(not published or job['revision']>published,'amend-revision-required')
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
        job['warnings']=[v for v in job['warnings'] if not v.startswith(('Citation locator unresolved:', 'No optional citation locators supplied;'))]
        for warning in evidence['warnings']:
            if warning not in job['warnings']:job['warnings'].append(warning)
        fm=page_metadata(markdown)
        for field in ('slug','title','doi','pmid'):
            require(same_identity(field,fm.get(field),job['identity'].get(field)),'candidate-identity-mismatch:'+field)
        require(fm.get('kind')=='paper','paper-kind-required')
        # Legacy content is recovery evidence, never a requirement on fresh synthesis.
        for field in ('authors','links'):fm.setdefault(field,[])
        if 'importance' in fm and not (type(fm['importance']) in (int,float) and 0<=fm['importance']<=1):
            fm.pop('importance')
            warning='Invalid optional importance omitted; scoring deferred.'
            if warning not in job['warnings']:job['warnings'].append(warning)
        fm['cited_by']=citation_backlinks(Path(config(runtime_root)['instance']),job['identity']['slug'])
        import yaml
        header=re.match(r'\A---\s*\n(.*?)\n---\s*\n',markdown,re.S)
        markdown='---\n'+yaml.safe_dump(fm,sort_keys=False,allow_unicode=True)+'---\n'+markdown[header.end():]
        require(re.search(r'^# '+re.escape(fm['title'])+r'\s*$',markdown,re.M),'paper-title-heading-required')
        require(not re.search(r'!\[|!\[\[|source-packages/|<img\b|portable-article-register|qualification-register',markdown,re.I),'article-payload-or-register-in-page')
        # Optional source locators are accepted only when they identify retained evidence.
        for sid,page in re.findall(r'\[source:([^:\]]+):(\d+)\]',markdown+'\n'+review_note):
            require(any(s['source_id']==sid and int(page) in s.get('selected_pages',[]) for s in job['sources']),'unresolved-source-reference')
        holds=[line.strip()[5:].strip() for line in review_note.splitlines() if line.strip().startswith('HOLD:')]
        drafts=work/'drafts'; drafts.mkdir(exist_ok=True)
        revision=max([job['revision']]+[int(p.name) for p in drafts.iterdir() if p.name.isdecimal()])+1
        draft=Path(tempfile.mkdtemp(prefix='.stage-',dir=drafts))
        from .archive import receipt_pointer
        receipt_name=receipt_pointer(config(runtime_root)['archive'],job_id+'-'+str(revision))
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
        from . import review
        check=review.once(dict(job,revision=revision),annotated,work,config(runtime_root).get('factual_check'))
        assess=check.get('revision')==revision and bool(check.get('text'))
        if assess:holds.append('Assess the independent factual findings against the source and stage once more with corrections or a reasoned disposition.')
        if check['status']!='success':
            warning='Independent factual check incomplete: '+check['status']+'; manuscript self-check remains the available review.'
            if warning not in job['warnings']:job['warnings'].append(warning)
        meta=dict(revision=revision,page_sha256=sha(draft/'page.md'),review_sha256=sha(draft/'review.txt'),
            citation_products={name:sha(draft/name) for name in ('annotated-page.md','citations.json')},
            receipt_name=receipt_name,material_issues=holds,source_hashes=[s['sha256'] for s in job['sources']],
            base_snapshot=str(base),base_sha256=job.get('apply_guard_sha256',job['original_sha256']))
        save(draft/'revision.json',meta)
        os.rename(draft,drafts/str(revision)); draft=drafts/str(revision)
        job.update(revision=revision,status='held' if holds else 'ready',blocking_reason='material-review-issues' if holds else None,
            next_action='Correct, qualify, or omit held claims and stage a new revision.' if holds else 'Publish this reviewed revision; archive verification precedes guarded page application.',
            artifacts=dict(revision=revision,draft=str(draft/'page.md'),diff=str(draft/'page.diff'),review=str(draft/'review.txt'),citations=str(draft/'citations.json'),annotated_draft=str(draft/'annotated-page.md')))
        job['artifacts']['integration_obligations']=integration_check(job,config(runtime_root),candidate=draft/'page.md',canonical=False)
        job['artifacts']['graph_follow_up']=graph_follow_up(job,config(runtime_root),candidate=draft/'page.md')
        job['artifacts']['factual_check']=check
        if assess and not any(line.strip().startswith('HOLD:') for line in review_note.splitlines()):
            job.update(blocking_reason='factual-review-pending',next_action=holds[-1])
        mark_time(job,'staged_at')
        store_job(job,runtime_root); return result(job,runtime_root)


def verifier_module():
    import importlib.util
    helper=Path(__file__).resolve().parents[2]/'skills/paper-ingest/scripts/verify_ingest.py'
    spec=importlib.util.spec_from_file_location('_manuscript_verify_ingest',helper)
    verifier=importlib.util.module_from_spec(spec); spec.loader.exec_module(verifier)
    return verifier


def citation_backlinks(instance,slug):
    """Rebuild only explicit citation edges; topic links are not citations."""
    import yaml
    target='papers/'+slug; found=[]
    for kind in ('papers','grants'):
        for path in sorted((instance/kind).glob('*.md')):
            if path==instance/(target+'.md'):continue
            try: fm=page_metadata(path.read_text())
            except (ValueError,yaml.YAMLError,UnicodeError):continue
            if isinstance(fm.get('cites'),list) and target in fm['cites']:
                found.append(kind+'/'+path.stem)
    return found


def integration_check(job,settings,*,candidate=None,canonical=True):
    """Publication blockers only; missing graph relationships are follow-up work."""
    import subprocess
    import sys
    verifier=verifier_module()
    page=Path(job['page']); text=Path(candidate or page).read_text(); fm=page_metadata(text)
    issues=verifier.filled_contract_checks(dict(fm,**{'needs-ingest':False}),text,page.stem)
    if canonical:
        argv=[sys.executable,'-B',verifier.__file__,page.stem,'--instance',settings['instance'],'--identity-only']
        if candidate:argv.extend(['--candidate',str(candidate)])
        if job.get('artifacts',{}).get('draft'):
            cache=Path(job['artifacts']['draft']).parent.parent.parent/'identity-cache'
            argv.extend(['--identity-cache',str(cache)])
        checked=subprocess.run(argv,capture_output=True,text=True,timeout=180)
        if checked.returncode:issues.append(checked.stdout[-12000:] or 'page-identity-check-failed')
    return issues


def graph_follow_up(job,settings,*,candidate=None):
    """Read-only observations; the existing propagation inbox owns later graph work."""
    import yaml
    verifier=verifier_module(); instance=Path(settings['instance'])
    fm=page_metadata(Path(candidate or job['page']).read_text()); issues=[]
    ledger_path=instance/'people/_ledger.yaml'
    try: ledger=yaml.safe_load(ledger_path.read_text()) if ledger_path.exists() else {}
    except (OSError,yaml.YAMLError):ledger={}; issues.append('author-ledger-unavailable')
    entries=ledger.get('entries',ledger.get('authors',[])) if isinstance(ledger,dict) else ledger or []
    if not isinstance(entries,list):entries=[]
    target='papers/'+Path(job['page']).stem
    authors=fm.get('authors') if isinstance(fm.get('authors'),list) else []
    if isinstance(fm.get('author_names'),list) and len(authors)<len(fm['author_names']):
        issues.append('author-associations-deferred')
    for author in authors:
        if not isinstance(author,str) or not verifier.AUTHOR_REF_RE.fullmatch(author):continue
        person=instance/(author+'.md'); edges=[]
        if person.exists():
            try:edges=page_metadata(person.read_text()).get('author_on',[])
            except (OSError,ValueError,yaml.YAMLError):pass
        else:
            entry=next((e for e in entries if isinstance(e,dict) and e.get('slug')==author.removeprefix('people/')),None)
            edges=entry.get('citations',[]) if entry else []
        if not isinstance(edges,list) or target not in edges:issues.append('author-edge-missing:'+author)
    for field in ('links','cited_by'):
        values=fm.get(field) or []
        if not isinstance(values,list):continue # invalid shape is a page blocker, not graph work
        for target in values:
            if field=='links' and verifier._is_external_url(target):continue
            if not isinstance(target,str) or not verifier.target_exists(str(instance),target):
                issues.append('missing-'+field+'-target:'+str(target))
    return issues


def record_event(job,settings,runtime_root):
    """Append once per published revision; preserve existing inbox text and comments."""
    import yaml
    from datetime import datetime,timezone
    lock=Path(runtime_root)/'integration'; lock.mkdir(exist_ok=True)
    with locked(lock):
        path=Path(settings['instance'])/'docs/rem-cycle/inbox.yaml'
        path.parent.mkdir(parents=True,exist_ok=True)
        raw=path.read_bytes() if path.exists() else None
        text=raw.decode() if raw is not None else 'items: []\n'
        value=yaml.safe_load(text)
        require(isinstance(value,dict) and isinstance(value.get('items'),list),'invalid-propagation-inbox')
        event_id='ingest-'+job['job_id']+'-'+str(job['revision'])
        target='papers/'+Path(job['page']).stem
        existing=next((e for e in value['items'] if isinstance(e,dict) and e.get('id')==event_id),None)
        if existing:
            require(existing.get('page')==target and existing.get('event')=='ingest','propagation-event-conflict')
            return
        event=dict(id=event_id,page=target,event='ingest',date=datetime.now(timezone.utc).date().isoformat(),consumed_by=[])
        if job.get('artifacts',{}).get('graph_follow_up'):event['graph_follow_up']=job['artifacts']['graph_follow_up']
        node=next(v for k,v in yaml.compose(text).value if k.value=='items')
        addition=yaml.safe_dump([event],sort_keys=False,allow_unicode=True)
        if node.flow_style:
            tokens=list(yaml.scan(text[node.start_mark.index:node.end_mark.index]))
            comma=',' if value['items'] and not isinstance(tokens[-3],yaml.tokens.FlowEntryToken) else ''
            addition=yaml.safe_dump(event,sort_keys=False,allow_unicode=True,default_flow_style=True,width=1000000).strip()
            offset=node.end_mark.index-1
            updated=text[:offset]+comma+'\n'+addition+'\n'+text[offset:]
        else:
            addition=''.join(' '*node.start_mark.column+line for line in addition.splitlines(True))
            offset=node.end_mark.index
            updated=text[:offset]+('' if text[:offset].endswith('\n') else '\n')+addition+text[offset:]
        require(yaml.safe_load(updated)['items']==value['items']+[event],'invalid-propagation-append')
        apply_bytes(path,updated.encode(),__import__('hashlib').sha256(raw).hexdigest() if raw is not None else None)


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
        require(job.get('blocking_reason')!='factual-review-pending','factual-review-pending')
        require(job.get('blocking_reason')!='sources-added-restage-required','sources-added-restage-required')
        if job.get('applied_revision'):require(job['applied_revision']==revision,'different-revision-already-applied')
        manifest=archive.build(job_id,revision,runtime_root=runtime_root); m=archive.verify(manifest)
        page=absolute(job['page']); root=manifest.parent; pending=root/'pending-page.md'; final=root/'page.md'
        if job['status']=='complete':
            archive.publication_check(manifest,json.loads((root/'publication.json').read_text()))
            require(archive.page_matches(final,page,root/'publication.json'),'completed-page-changed')
            return result(job,runtime_root)
        require(m['receipt_name'].startswith('r2://'),'restage-legacy-draft-for-external-receipt; retain the same job and sources')
        if hold_live_edit(job,work):
            store_job(job,runtime_root); return result(job,runtime_root)
        issues=integration_check(job,settings,candidate=work/'drafts'/str(revision)/'page.md',canonical=False)
        if issues:
            job.update(status='integration-pending' if job.get('applied_revision') else 'ready',blocking_reason='integration-obligations',
                next_action='Correct the reported page fields through stage, then publish the same job; graph maintenance is deferred.',
                artifacts={**job['artifacts'],'integration_obligations':issues})
            store_job(job,runtime_root); return result(job,runtime_root)
        job['artifacts']['graph_follow_up']=graph_follow_up(job,settings,candidate=work/'drafts'/str(revision)/'page.md')
        publication_path=root/'publication.json'
        try:
            if publication_path.exists():pub=archive.publication_check(manifest,json.loads(publication_path.read_text()))
            else:
                pub=archive.publish(manifest,destination=settings['archive']); save(publication_path,pub)
            archive.retain_receipt(publication_path,destination=settings['archive'],pointer=m['receipt_name'])
        except (ValueError,OSError,KeyError) as exc:
            job.update(status='publication-pending',blocking_reason=str(exc),next_action='Retry publish after archive availability/configuration is corrected; no inference will repeat.')
            store_job(job,runtime_root); return result(job,runtime_root)
        current=sha(page) if page.exists() else None
        if current not in (job.get('apply_guard_sha256',job['original_sha256']),sha(pending),sha(final)):
            hold_live_edit(job,work)
            store_job(job,runtime_root); return result(job,runtime_root)
        receipt=publication_path
        mark_time(job,'archive_verified_at')
        job.update(status='integration-pending',next_action='Resolve only the reported integration obligations, then retry publish without redrafting.',blocking_reason=None)
        mark_time(job,'integration_started_at')
        try: issues=integration_check(job,settings,candidate=work/'drafts'/str(revision)/'page.md')
        except Exception as exc:issues=['integration-check-unavailable:'+type(exc).__name__]
        if issues:
            job.update(blocking_reason='integration-obligations',artifacts={**job['artifacts'],'integration_obligations':issues,'manifest':str(manifest),'receipt':str(receipt)})
            if any('temporarily-unavailable' in issue for issue in issues):
                job.update(blocking_reason='metadata-temporarily-unavailable',next_action='Retain this job and revision; defer the canonical lookup and retry publish in a later authorized run. Do not redraft or sleep-loop.')
        else:
            current=sha(page) if page.exists() else None
            if current not in (job.get('apply_guard_sha256',job['original_sha256']),sha(pending),sha(final)):
                hold_live_edit(job,work)
                store_job(job,runtime_root); return result(job,runtime_root)
            if current==job.get('apply_guard_sha256',job['original_sha256']):apply_bytes(page,pending.read_bytes(),current)
            job['applied_revision']=revision
            store_job(job,runtime_root)
            current=sha(page)
            require(current in (sha(pending),sha(final)),'concurrent-page-edit')
            try:record_event(job,settings,runtime_root)
            except (OSError,ValueError) as exc:
                job.update(status='integration-pending',blocking_reason='propagation-event-pending',next_action='Correct the inbox issue, then retry publish; do not redraft.',artifacts={**job['artifacts'],'integration_obligations':[str(exc)]})
                store_job(job,runtime_root); return result(job,runtime_root)
            if current!=sha(final):apply_bytes(page,final.read_bytes(),current)
            else:require(sha(page)==current,'concurrent-page-edit')
            job.update(status='complete',blocking_reason=None,next_action='Ingestion is complete; commit the reviewed owned page and integration edits using git-ops; receipt metadata stays external.',
                published_revision=revision,
                artifacts={**job['artifacts'],'manifest':str(manifest),'receipt':str(receipt),'integration_obligations':[]})
            mark_time(job,'completed_at')
        store_job(job,runtime_root); return result(job,runtime_root)
