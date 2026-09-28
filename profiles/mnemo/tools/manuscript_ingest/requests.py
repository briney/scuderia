"""One shared ledger; a reservation is consumed before any network dispatch."""
import json
import sqlite3
from article_archive_compat.article_runtime import digest, outside_instance, require


def key(*,sources,operation,selection,model,prompt,settings):
    return digest(dict(sources=sources,operation=operation,selection=selection,model=model,prompt=prompt,settings=settings))


def connect(ledger):
    ledger=outside_instance(ledger); ledger.parent.mkdir(parents=True,exist_ok=True)
    db=sqlite3.connect(ledger,timeout=30,isolation_level=None)
    db.execute('CREATE TABLE IF NOT EXISTS requests (key TEXT PRIMARY KEY, job TEXT NOT NULL, predecessor TEXT, status TEXT NOT NULL, outcome TEXT)')
    return db


def reserve(request_key,*,ledger,job_id,authorization):
    require(type(authorization.get('max_requests')) is int and authorization['max_requests']>=0,'invalid-request-budget')
    predecessor=None
    # Only internal callers pass deployment/operator authorization. Never in tool schema.
    if authorization.get('retry_id'):
        require(authorization.get('retry_key')==request_key,'retry-scope-mismatch')
        predecessor=request_key
        request_key=digest(dict(predecessor=request_key,authorization=authorization['retry_id']))
    db=connect(ledger)
    try:
        db.execute('BEGIN IMMEDIATE')
        row=db.execute('SELECT status,outcome,predecessor FROM requests WHERE key=?',(request_key,)).fetchone()
        if row:
            return dict(dispatch=False,key=request_key,status=row[0],outcome=json.loads(row[1]) if row[1] else None,predecessor=row[2])
        if predecessor:
            prior=db.execute('SELECT status FROM requests WHERE key=?',(predecessor,)).fetchone()
            require(prior and prior[0] in ('failed','uncertain'),'retry-needs-failed-or-uncertain-predecessor')
        count=db.execute('SELECT COUNT(*) FROM requests WHERE job=?',(job_id,)).fetchone()[0]
        if count>=authorization['max_requests']:
            return dict(dispatch=False,key=request_key,status='budget-exhausted',outcome=None,predecessor=predecessor)
        db.execute('INSERT INTO requests VALUES (?,?,?,?,NULL)',(request_key,job_id,predecessor,'uncertain'))
        db.commit()
        return dict(dispatch=True,key=request_key,status='uncertain',outcome=None,predecessor=predecessor)
    finally:
        db.close()


def finish(request_key,*,ledger,outcome):
    require(outcome.get('status') in ('success','partial','failed','uncertain'),'invalid-request-outcome')
    raw=json.dumps(outcome,allow_nan=False,ensure_ascii=False)
    db=connect(ledger)
    try:
        db.execute('BEGIN IMMEDIATE')
        row=db.execute('SELECT status,outcome FROM requests WHERE key=?',(request_key,)).fetchone()
        require(row is not None,'request-not-reserved')
        if row[1] is not None:
            require(row[1]==raw,'request-outcome-already-recorded')
        else: db.execute('UPDATE requests SET status=?,outcome=? WHERE key=?',(outcome['status'],raw,request_key))
        db.commit()
    finally: db.close()


def inspect_once(*,images,question,configuration,output):
    """Reuse the single-POST vision transport, retaining free text and partial output."""
    import importlib.util
    import os
    from pathlib import Path
    from .workflow import save
    client_path=Path(__file__).resolve().parents[2]/'skills/paper-ingest/scripts/paper-vision/client.py'
    spec=importlib.util.spec_from_file_location('_manuscript_vision_transport',client_path)
    client=importlib.util.module_from_spec(spec); spec.loader.exec_module(client)
    output.mkdir(parents=True,exist_ok=True)
    credential=os.environ.get(configuration.get('credential_env','LITELLM_API_KEY'),'')
    require(credential and credential.isascii() and all(32<ord(c)<127 for c in credential),'inspection-credential-unavailable')
    require(credential not in question,'credential-in-input')
    rows=[]; raws=[]
    for image in images:
        raw,row=client.read_image(str(image['path'])); row['label']=image['label']; rows.append(row); raws.append(raw)
    recipe=dict(settings=dict(configuration.get('settings',{}),model=configuration['model']),endpoint=configuration['endpoint'],timeout_seconds=configuration.get('timeout_seconds',120))
    record=dict(question=question,images=rows,recipe=recipe,prompt=configuration['prompt'])
    save(output/'input.json',record)
    status,raw=client.post(client.build_wire(record,raws),credential,recipe)
    result=dict(status='failed',text=None,usage=None,http_status=status,warnings=[])
    try:
        envelope,error=client.retain_response(output,raw,credential,result)
        require(error is None,'invalid-inspection-response')
        envelope=client.scrub(envelope,credential); choice=envelope['choices'][0]
        require(status==200 and envelope.get('model')==configuration['model'],'inspection-response-identity')
        text=choice['message']['content']; require(isinstance(text,str) and text.strip(),'empty-inspection')
        require(not choice['message'].get('tool_calls'),'unexpected-inspection-tool-call')
        result.update(status='success' if choice.get('finish_reason')=='stop' else 'partial',text=text,
            usage=envelope.get('usage'),finish_reason=choice.get('finish_reason'))
        if result['status']=='partial':result['warnings'].append('Truncated observation; not complete evidence.')
    except (ValueError,KeyError,TypeError,IndexError):result['warnings'].append('Unusable optional response; safely sanitized evidence retained without invented repair.')
    save(output/'outcome.json',result)
    return result
