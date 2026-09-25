#!/usr/bin/env python3
"""Fixed-argument child entry. Deployment roots are supplied by trusted launcher."""
import argparse
import json
from pathlib import Path
import sys


def bootstrap(enrichment_root, adapter_dir, method):
    for path, marker in ((enrichment_root,'pdf_enrichment/__init__.py'),
                         (adapter_dir,'source_package.py'),(method,'pdf_source_package/__init__.py')):
        path=Path(path)
        if not path.is_absolute() or '..' in path.parts or not (path/marker).is_file():
            raise ValueError('trusted-deployment-path-required')
        if any(p.is_symlink() for p in (path,*path.parents)):
            raise ValueError('trusted-root-symlink-forbidden')
    sys.path[:0]=[str(enrichment_root),str(adapter_dir)]
    import pdf_enrichment
    if Path(pdf_enrichment.__file__).resolve().parent != Path(enrichment_root)/'pdf_enrichment':
        raise ValueError('different-enrichment-already-imported')
    # Pin executable method code from deployment before any evidence is read.
    # Frozen v7 rejects a different method once the trusted package is loaded.
    from pdf_enrichment import trusted
    trusted.module('counting', method)


def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('enrichment-root','adapter-dir','method','receipt'): p.add_argument('--'+name,required=True)
    p.add_argument('--offline',action='store_true')
    sub=p.add_subparsers(dest='operation',required=True)
    def command(name,required,optional=()):
        c=sub.add_parser(name)
        for field in required: c.add_argument('--'+field,required=True)
        for field in optional: c.add_argument('--'+field)
        return c
    command('prepare',('source-handoff','output'),('test-root',))
    command('count',('job','processor-cache'))
    command('seal',('job',))
    c=command('execute',('job','approval')); c.add_argument('--authorize-posts',action='store_true')
    command('report',('job','output'))
    command('import-test-response',('job','responses'))
    command('review-create',('run','output'),('kind',))
    c=command('review-packet',('review-root','output')); c.add_argument('--element',action='append',required=True); c.add_argument('--max-bytes',type=int,default=1000000)
    command('review-import',('review-root','packet','submission'))
    command('export',('review-root','output'))
    command('verify-export',('export-path',))
    c=command('consume',('export-path','element','target','purpose','output'),('qualification','source-inspection'))
    c.add_argument('--aspect',action='append')
    args=p.parse_args(argv)
    try:
        bootstrap(args.enrichment_root,args.adapter_dir,args.method)
        from qualified_enrichment import runtime,reviews,exports
        from qualified_enrichment.storage import absolute,load,save,sha,offline,tree
        from qualified_enrichment.records import require
        from pdf_enrichment import live,importer,bindings
        # All non-POST operations are offline by construction, not by operator preference.
        if args.offline or args.operation!='execute': offline()
        artifacts={}; details={}; exit_code=0
        if args.operation=='prepare':
            details=runtime.prepare(args.source_handoff,args.output,args.method,args.test_root)
            artifacts[str(absolute(args.output)/'selection.json')]=sha(absolute(args.output)/'selection.json')
        elif args.operation in ('count','seal','execute','report','import-test-response'):
            job=absolute(args.job); state=runtime.read_job(job)
            run=job/'v7'
            if args.operation != 'report':
                from qualified_enrichment.storage import code_hashes
                require(state['selection']['code'] == code_hashes(), 'selection-code-binding')
            require(state['selection']['selected'], 'zero-eligible-no-enrichment-operation-required')
            if args.operation=='count':
                live.count(run,absolute(args.processor_cache)); names=['counts.json','counts.sha256']
            elif args.operation=='seal':
                live.seal(run); names=['seal.json','approval.template.json']
            elif args.operation=='execute':
                result=live.execute(run,absolute(args.approval),authorize=args.authorize_posts)
                names=['execution-session.json','executed-approval.json','execution-complete.json']
                expected=load(run/'approval.template.json')['requests']
                exit_code=0 if len(result['attempted'])==len(expected) and all(v.get('complete') for v in result['results'].values()) else 1
            elif args.operation=='import-test-response':
                importer.import_test_response(run,absolute(args.responses)); names=['enrichment-results.json']
            else:
                from qualified_enrichment.storage import external
                external(args.output,[job,absolute(state['source_package'])])
                importer.report(run,absolute(args.output)); names=[]
                for name in tree(absolute(args.output)): artifacts[str(absolute(args.output)/name)]=sha(absolute(args.output)/name)
            for name in names: artifacts[str(run/name)]=sha(run/name)
            # Use the frozen validators after the operation too; filenames alone
            # do not establish count, outcome or source validity.
            if args.operation=='count': live.verify_counts(run,bindings.verify(run))
            else: runtime.read_job(job)
        elif args.operation=='review-create':
            details=reviews.create(args.run,args.kind or 'qualified-job',args.output)
            artifacts[str(absolute(args.output)/'dossier.json')]=sha(absolute(args.output)/'dossier.json')
        elif args.operation=='review-packet':
            details=reviews.packet(args.review_root,args.element,args.output,args.max_bytes)
            artifacts[str(absolute(args.output))]=sha(args.output)
        elif args.operation=='review-import':
            result=reviews.import_review(args.review_root,args.packet,args.submission)
            path=absolute(args.review_root)/'decisions'/f'{result["sequence"]:06d}.json'
            artifacts[str(path)]=sha(path)
        elif args.operation=='export':
            details=exports.export(args.review_root,args.output)
            exports.verify_export(absolute(args.output)/'handoff.json',production=False)
            for name in ('handoff.json','annotated.html'): artifacts[str(absolute(args.output)/name)]=sha(absolute(args.output)/name)
        elif args.operation=='verify-export':
            details=exports.verify_export(args.export_path,production=False)
            artifacts[str(absolute(args.export_path))]=sha(args.export_path)
        else:
            value=exports.verify_export(args.export_path,production=False)
            views={v['element_id']:v for v in value['elements']}
            require(args.element in views,'unknown-consumer-element')
            inspection=load(absolute(args.source_inspection)) if args.source_inspection else None
            details=exports.exact_view(views[args.element],args.target,purpose=args.purpose,aspects=args.aspect or ['content'],
                                      qualification=args.qualification,source_inspection=inspection)
            from qualified_enrichment.storage import external
            dossier=load(absolute(value['review_root'])/'dossier.json')
            external(args.output,[absolute(args.export_path).parent,absolute(value['review_root']),
                                  absolute(value['source_package']),absolute(dossier['snapshot']['path'])])
            save(absolute(args.output),details); artifacts[str(absolute(args.output))]=sha(args.output)
        receipt=dict(schema='enrichment-operation-receipt-v1',operation=args.operation,exit_code=exit_code,
                     checked_artifacts=artifacts,artifact_status='verified',
                     production_executed=False if args.operation!='execute' else None,
                     note='Actual child operation; no scientific correctness or acceptance asserted.')
        if args.operation == 'review-packet':
            from qualified_enrichment.records import digest
            receipt['review_packet_sha256'] = digest(details)
        save(absolute(args.receipt),receipt)
        print(json.dumps(receipt,ensure_ascii=False)); return exit_code
    except (ValueError,OSError,KeyError,TypeError,RuntimeError,ImportError) as exc:
        print(json.dumps(dict(status='hold',error_type=type(exc).__name__,diagnostic=str(exc)))); return 2


if __name__=='__main__': raise SystemExit(main())
