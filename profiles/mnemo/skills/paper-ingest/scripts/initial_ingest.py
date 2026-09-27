"""Durable initial-ingest continuations over existing native operations; no executor."""
import copy
import os
from pathlib import Path
import article_enrichment as ae
import portable_articles as pa
from article_runtime import absolute, require, sha

SCHEMA='initial-ingest-plan-v1'


def plan(article, *, page, work_root, identity):
    work=absolute(work_root); page=absolute(page)
    if work.exists():
        saved=ae.read_bound(work/'plan.json')
        require(saved['schema']==SCHEMA and saved['article']==article and saved['page']==str(page),'initial-route-binding')
        return status(work)
    pa.article_key(dict(slug=article))
    pa.new_directory(work)
    value=dict(schema=SCHEMA,route='initial-ingest',article=article,page=str(page),
        page_sha256=sha(page) if page.exists() else None,identity=identity,
        processing_policy='manuscript-only-v1',planned_at=pa.now_utc())
    ae._seal_file(work/'plan.json',value)
    if page.exists(): pa.put(work/'original-page.md',page.read_bytes())
    pa.save(work/'acquisition.template.json',dict(schema='acquired-sources-v2',
        article=identity or dict(slug=article,title=None,doi=None,pmid=None,version=None),files=[],attempts=[],
        obligations=dict(body=None,manuscript=None),attachments=dict(status='not-inspected',items=[]),
        processing=dict(policy='manuscript-only-v1',manuscript=dict(source_id=None,pages=[],basis=None))))
    return status(work)


def attempts(work_root):
    work=absolute(work_root); result=dict(source=[],enrichment=[])
    for path in sorted((work/'registered-attempts').glob('*.json')):
        row=ae.read_bound(path)
        require(row['plan_sha256']==sha(work/'plan.json'),'attempt-plan-binding')
        root=absolute(row['path']); require(root.is_relative_to(work),'attempt-outside-workflow')
        if str(root) not in result[row['kind']]: result[row['kind']].append(str(root))
    return result


def record_attempt(work_root, *, kind, path):
    work=absolute(work_root); value=ae.read_bound(work/'plan.json')
    require(value['schema']==SCHEMA and kind in ('source','enrichment'),'initial-attempt-kind')
    path=absolute(path); require(path.is_dir() and path.is_relative_to(work) and path!=work,'attempt-outside-workflow')
    import operation_timing
    operation_timing.summarize(**{kind+'_attempts':[path]})
    directory=work/'registered-attempts'; directory.mkdir(exist_ok=True)
    key=pa.digest(dict(kind=kind,path=str(path)))
    target=directory/(key+'.json')
    if not target.exists(): ae._seal_file(target,dict(kind=kind,path=str(path),plan_sha256=sha(work/'plan.json')))
    return attempts(work)


def _attempt(work, step):
    return work.parent/(work.name+'-attempts')/step


def _operation(work, step, tool, operation, *, missing=(), artifacts=None, **args):
    attempt=_attempt(work,step)
    if (attempt/'job.json').exists():
        import operation_jobs
        state=operation_jobs.status(attempt)
        if state['status'] in ('starting','running','uncertain'):
            return dict(tool=tool,operation='status',attempt_dir=str(attempt),missing_inputs=[],job=state)
        if state['status']=='failed':
            return dict(tool=tool,operation='status',attempt_dir=str(attempt),missing_inputs=['inspect-failed-attempt-no-retry'],job=state)
    return dict(tool=tool,operation=operation,attempt_dir=str(attempt),background=True,
        missing_inputs=list(missing),artifacts=artifacts or {},**args)


def status(work_root):
    work=absolute(work_root); p=ae.read_bound(work/'plan.json'); require(p['schema']==SCHEMA,'initial-plan-required')
    def native(step,operation,tool='paper_enrichment',missing=(),artifacts=None,**args):
        return _operation(work,step,tool,operation,missing=missing,artifacts=artifacts,**args)
    def article(step,missing=(),**args):
        return native(step,'article',missing=missing,arguments=dict(command=step,work_root=str(work),**args))
    # Only this plan's generated operation namespace is inspected, never historical runs.
    operations=work.parent/(work.name+'-attempts')
    for attempt in sorted(operations.glob('*/job.json')):
        if not (attempt.parent/'terminal.json').exists():
            import operation_jobs
            active=operation_jobs.status(attempt.parent)
            kind=operation_jobs.load_job(attempt.parent)[1]['identity']['kind']
            return dict(schema=SCHEMA,route=p['route'],article=p['article'],page=p['page'],
                completion_verifier='final_products.verify_ingest',production_complete=False,next_step='operation-status',
                next_operation=dict(tool='paper_workflow' if kind=='source' else 'paper_enrichment',operation='status',
                    attempt_dir=str(attempt.parent),missing_inputs=[]),execution=active)
    cache=os.environ.get('REENRICH_PROCESSOR_CACHE') or os.environ.get('PDF_PROCESSOR_CACHE')
    cache_args=dict(processor_cache=str(absolute(cache))) if cache else {}
    source=work/'source'; job=work/'enrichment-job'; review=work/'review'; export=work/'export'
    op=None; step='source-acquisition'
    if not (work/'retention/retention.json').exists():
        op=article('initial-retain',missing=['acquisition.json','application_endpoint','max_application_posts'])
        op['artifacts']['acquisition_template']=str(work/'acquisition.template.json')
    elif not (source/'manifest.json').exists():
        step='source-prepare'; op=native(step,'prepare',tool='paper_workflow',scope_path=str(work/'retention/scope.json'),output_dir=str(source),**cache_args)
    elif not (work/'source-handoff/handoff.json').exists():
        record_attempt(work,kind='source',path=source)
        from pdf_source_package import reporting, gates
        evidence=reporting.Evidence(source); reporting.source_facts(evidence)
        for phase in ('initial','classification','association'):
            step='source-'+phase
            if not (source/(phase+'-plan.json')).exists():
                op=native(step+'-prepare','prepare-stage',tool='paper_workflow',package_dir=str(source),phase=phase,**cache_args); break
            facts,_=reporting.basic_phase(evidence,phase)
            if (source/(phase+'-complete.json')).exists(): continue
            next_step=gates.next_step(source,phase,facts)
            if next_step=='hold-inspect-evidence-no-retry':
                op=dict(missing_inputs=['inspect-source-evidence-no-retry']); break
            if next_step=='review-and-author-approval':
                op=native(step+'-execute','execute',tool='paper_workflow',package_dir=str(source),phase=phase,
                    missing=['approval_path','authorize_posts'],artifacts=dict(approval_template=str(source/(phase+'-approval.template.json')))); break
            op=native(step+'-seal','seal',tool='paper_workflow',package_dir=str(source),phase=phase,
                missing=[] if cache else ['processor_cache'],**cache_args); break
        evidence.check()
        if op is None:
            step='source-report'
            if not (_attempt(work,step)/'worker/result.json').exists():
                op=native(step,'report',tool='paper_workflow',package_dir=str(source))
            else: step='initial-handoff'; op=article(step)
    elif not (job/'selection.json').exists():
        step='enrichment-prepare'; op=native(step,'prepare',source_handoff=str(work/'source-handoff/handoff.json'),output=str(job),**cache_args)
    elif not (review/'dossier.json').exists():
        from qualified_enrichment import runtime
        state=runtime.read_job(job); record_attempt(work,kind='enrichment',path=job)
        if not (job/'enrichment/seal.json').exists() and state['selection']['selected']:
            step='enrichment-seal'; op=native(step,'seal',job=str(job),missing=[] if cache else ['processor_cache'],**cache_args)
        elif not (job/'enrichment/execution-start.json').exists() and state['selection']['selected']:
            step='enrichment-execute'; op=native(step,'execute',job=str(job),missing=['approval','authorize_posts'],
                artifacts=dict(approval_template=str(job/'enrichment/approval.template.json')))
        else:
            attempt=_attempt(work,'enrichment-execute')
            if (attempt/'job.json').exists():
                import operation_jobs
                running=operation_jobs.status(attempt)
                if running['status'] in ('starting','running','uncertain'):
                    op=dict(tool='paper_enrichment',operation='status',attempt_dir=str(attempt),missing_inputs=[])
            if op is None:
                step='review-create'; op=native(step,'review-create',run=str(job),output=str(review),kind='qualified-job')
    elif not (export/'handoff.json').exists():
        from qualified_enrichment import reviews
        dossier=reviews.verify(review)
        if not (work/'review-packet.json').exists():
            step='review-packet'; op=native(step,'review-packet',review_root=str(review),output=str(work/'review-packet.json'),elements=[e['element_id'] for e in dossier['snapshot']['elements']])
        elif not list((review/'decisions').glob('*.json')):
            step='review-import'; op=native(step,'review-import',review_root=str(review),packet=str(work/'review-packet.json'),missing=['submission'])
        else:
            step='export'; op=native(step,'export',review_root=str(review),output=str(export))
    elif not (work/'enriched-handoff/handoff.json').exists():
        step='initial-enriched-handoff'; op=native(step,'article',arguments=dict(command='initial-handoff',work_root=str(work),enriched=True))
    elif not (work/'final-products/manifest.json').exists(): step='initial-finalize'; op=article(step)
    elif not (work/'publication.json').exists():
        step='initial-publish'; op=article(step,missing=['remote','bucket','prefix'])
    else:
        step='verify-ingest'; op=dict(missing_inputs=['scientific-page-review','bibliography-authors-graph','verify_ingest.py'],
            artifacts=dict(manifest=str(work/'final-products/manifest.json'),publication_receipt=str(work/'publication.json')))
    return dict(schema=SCHEMA,route=p['route'],article=p['article'],page=p['page'],
        completion_verifier='final_products.verify_ingest',production_complete=False,next_step=step,next_operation=op,
        elapsed_seconds=__import__('operation_timing').seconds(p['planned_at'],pa.now_utc()))


def operate(command, work_root, **args):
    """Fixed adapters to existing validators/finalizers, invoked by native launcher."""
    import source_package as sp
    import final_products as fp
    work=absolute(work_root); p=ae.read_bound(work/'plan.json'); require(p['schema']==SCHEMA,'initial-plan-required')
    code=Path(__file__).resolve().parent
    if command=='initial-retain':
        acquisition=sp.load(work/'acquisition.json'); require(acquisition['article']['slug']==p['article'],'initial-article-binding')
        require(acquisition['schema']=='acquired-sources-v2','initial-manuscript-policy-required')
        if p['identity']: require(acquisition['article']==p['identity'],'initial-identity-changed')
        sp.prepare(work/'acquisition.json',work/'retention',args['application_endpoint'],args['max_application_posts'])
    elif command=='initial-handoff':
        common=dict(retention_path=work/'retention/retention.json',package=work/'source',
            launcher_result=_attempt(work,'source-report')/'worker/result.json',method=code)
        if args.get('enriched'):
            value=sp.build_enriched_handoff(**common,enrichment_handoff=work/'export/handoff.json',
                enrichment_launcher_result=_attempt(work,'export')/'worker/result.json',integration=code,enrichment_root=code)
            output=work/'enriched-handoff'
        else: value=sp.build_handoff(**common); output=work/'source-handoff'
        pa.new_directory(output); pa.save(output/'handoff.json',value); pa.put(output/'summary.txt',value['summary'].encode())
        if 'qualifications' in value: pa.put(output/'qualifications.txt',value['qualifications'].encode())
    elif command=='initial-finalize':
        registered=attempts(work)
        fp.from_ingest(work/'enriched-handoff/handoff.json',work/'final-products',method=code,integration=code,enrichment_root=code,
            source_attempts=registered['source'],enrichment_attempts=registered['enrichment'])
    elif command=='initial-publish':
        fp.publish_ingest(work/'final-products/manifest.json',work/'publication.json',args['remote'],args['bucket'],args['prefix'])
    elif command=='initial-record-attempt': record_attempt(work,**args)
    else: raise ValueError('unknown-initial-operation')
    return status(work)
