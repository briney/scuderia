"""Operator-only extraction. Never registered in the ordinary ingestion toolset."""
import json
import re
from pathlib import Path
from . import workflow as w, archive, requests


def authorized(scope,runtime_root):
    configured=w.config(runtime_root).get('targeted_scopes',{})
    w.require(isinstance(scope,dict) and scope.get('id') in configured and configured[scope['id']]==scope,'trusted-operator-scope-required')
    w.require(set(scope)=={'id','manifest','manifest_sha256','selections','objective','budget'},'invalid-targeted-scope')
    w.require(type(scope['budget']) is int and 0<scope['budget']<=4,'bounded-targeted-budget-required')
    w.require(isinstance(scope['objective'],str) and scope['objective'].strip() and not re.search(r'\*|all eligible|everything',scope['objective'],re.I),'explicit-target-objective-required')
    selections=scope['selections']; w.require(isinstance(selections,list) and 0<len(selections)<=4,'explicit-target-selection-required')
    manifest=w.absolute(scope['manifest']); w.require(w.sha(manifest)==scope['manifest_sha256'],'target-manifest-changed')
    m=archive.verify(manifest)
    for selection in selections:
        w.require(set(selection)=={'source_id','page','item'} and isinstance(selection['item'],str) and selection['item'].strip() and not re.search(r'\*|all|everything',selection['item'],re.I),'explicit-target-item-required')
        source=next((s for s in m['sources'] if s['source_id']==selection['source_id']),None)
        w.require(source is not None and type(selection['page']) is int and selection['page']>0,'target-source-scope')
        # Supplemental originals were intentionally not parsed by ordinary ingestion.
        import pymupdf
        with pymupdf.open(manifest.parent/source['key']) as pdf:w.require(selection['page']<=len(pdf),'target-page-scope')
    return m


def start(request,*,invocation_scope,runtime_root):
    w.require(request==invocation_scope,'targeted-request-cannot-broaden-scope')
    authorized(invocation_scope,runtime_root)
    job_id=w.digest(invocation_scope)[:32]; root=w.absolute(runtime_root)/'targeted'/job_id; root.mkdir(parents=True,exist_ok=True)
    with w.locked(root):
        path=root/'job.json'
        if path.exists():w.require(json.loads(path.read_text())['scope']==invocation_scope,'targeted-scope-changed')
        else:w.save(path,dict(job_id=job_id,scope=invocation_scope,revision=0))
    return dict(job_id=job_id,status='ready',next_action='Operator may run this exact selection; no paper rewrite.')


def load(job_id,runtime_root):
    w.require(isinstance(job_id,str) and re.fullmatch('[a-f0-9]{32}',job_id),'invalid-targeted-job-id')
    root=w.absolute(runtime_root)/'targeted'/job_id
    w.require((root/'job.json').is_file(),'not-a-targeted-job')
    job=json.loads((root/'job.json').read_text()); authorized(job['scope'],runtime_root)
    return root,job


def run(job_id,*,runtime_root):
    root,job=load(job_id,runtime_root)
    with w.locked(root):
        if (root/'result.json').exists():return json.loads((root/'result.json').read_text())
        scope=job['scope']; m=authorized(scope,runtime_root); cfg=w.config(runtime_root).get('vision')
        w.require(cfg,'targeted-inspection-unavailable')
        key=requests.key(sources=sorted(s['sha256'] for s in m['sources'] if s['source_id'] in {x['source_id'] for x in scope['selections']}),
            operation='targeted-extraction',selection=dict(selections=scope['selections'],objective=scope['objective']),model=cfg['model'],prompt=cfg['prompt'],settings=cfg.get('settings',{}))
        ledger=w.absolute(runtime_root)/'requests.sqlite'
        reserved=requests.reserve(key,ledger=ledger,job_id=job_id,authorization={'max_requests':scope['budget']})
        if reserved['dispatch']:
            import pymupdf
            images=[]
            try:
                for number,selection in enumerate(scope['selections']):
                    source=next(s for s in m['sources'] if s['source_id']==selection['source_id']); image=root/(str(number)+'.png')
                    with pymupdf.open(Path(scope['manifest']).parent/source['key']) as pdf:pdf[selection['page']-1].get_pixmap(matrix=pymupdf.Matrix(1.5,1.5)).save(image)
                    images.append(dict(path=image,label=json.dumps(selection)))
                outcome=requests.inspect_once(images=images,question=scope['objective']+'\nExtract only these items: '+json.dumps(scope['selections']),configuration=cfg,output=root/'request')
            except Exception:outcome=dict(status='uncertain',text=None,warnings=['Target request did not finish. No automatic repeat.'])
            requests.finish(reserved['key'],ledger=ledger,outcome=outcome)
        else:outcome=reserved['outcome'] or dict(status=reserved['status'],text=None)
        result=dict(job_id=job_id,**outcome,source_references=scope['selections'],request_key=reserved['key'])
        w.save(root/'result.json',result);return result


def revise(job_id,text,*,runtime_root):
    root,job=load(job_id,runtime_root)
    w.require(isinstance(text,str) and text.strip() and (root/'result.json').exists(),'target-result-and-revision-required')
    with w.locked(root):
        job['revision']+=1; w.save(root/('revision-'+str(job['revision'])+'.json'),dict(text=text,source_references=job['scope']['selections']))
        w.save(root/'job.json',job)
    return dict(job_id=job_id,revision=job['revision'])


def main():
    import argparse
    p=argparse.ArgumentParser(description='Operator-only, deployment-scoped target extraction.')
    p.add_argument('--runtime-root',type=Path,required=True); p.add_argument('--scope',required=True)
    args=p.parse_args(); scope=w.config(args.runtime_root).get('targeted_scopes',{}).get(args.scope)
    w.require(scope is not None,'operator-scope-not-configured')
    job=start(scope,invocation_scope=scope,runtime_root=args.runtime_root)
    print(json.dumps(run(job['job_id'],runtime_root=args.runtime_root),ensure_ascii=False))

if __name__=='__main__':main()
