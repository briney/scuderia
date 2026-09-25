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
    import os
    os.environ.update(PDF_ENRICHMENT_METHOD=str(method), REENRICH_ENRICHMENT_ROOT=str(enrichment_root),
                      REENRICH_INTEGRATION_ROOT=str(Path(__file__).resolve().parent))
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
    command('prepare',('source-handoff','output'),('test-root','processor-cache'))
    command('count',('job','processor-cache'))
    command('seal',('job',),('processor-cache',))
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
        artifacts={}; details={}; exit_code=0; next_step=None
        if args.operation=='prepare':
            details=runtime.prepare(args.source_handoff,args.output,args.method,args.test_root)
            job=absolute(args.output)
            if args.processor_cache or not details['selected']:
                next_step=runtime.prepare_for_approval(job,args.processor_cache)
                for name in tree(job): artifacts[str(job/name)]=sha(job/name)
            else:
                next_step='seal-with-processor-cache'
                artifacts[str(job/'selection.json')]=sha(job/'selection.json')
        elif args.operation in ('count','seal','execute','report','import-test-response'):
            job=absolute(args.job); state=runtime.read_job(job)
            if state['selection']['schema']=='qualified-selection-v1':
                require(args.operation=='report','historical-job-read-only-new-job-required')
                from qualified_enrichment.storage import external
                external(args.output,[job,absolute(state['source_package'])])
                importer.report(job/'v7',absolute(args.output))
                for name in tree(absolute(args.output)): artifacts[str(absolute(args.output)/name)]=sha(absolute(args.output)/name)
            else:
                import article_enrichment as ae
                _,manifest,binding=runtime.portable_job(job,for_execution=args.operation!='report')
                run=job/'enrichment'
                if args.operation=='count':
                    ae.count(job,binding,manifest,cache=absolute(args.processor_cache))
                elif args.operation=='seal':
                    next_step=runtime.prepare_for_approval(job,args.processor_cache)
                elif args.operation=='execute':
                    result=ae.execute(job,binding,manifest,absolute(args.approval),authorize=args.authorize_posts)
                    exit_code=0 if result['accounting']['complete'] else 1
                    details=result['accounting']
                elif args.operation=='import-test-response':
                    raise ValueError('portable-fixtures-use-offline-executor-double')
                else:
                    from qualified_enrichment.storage import external,new
                    output=new(args.output,[job,absolute(state['source_package'])])
                    save(output/'report.json',state)
                    artifacts[str(output/'report.json')]=sha(output/'report.json')
                if args.operation!='report':
                    for name in tree(run):
                        if not name.endswith('.lock'): artifacts[str(run/name)]=sha(run/name)
                    runtime.read_job(job)
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
        if next_step is not None: receipt['next_step']=next_step
        if args.operation == 'review-packet':
            from qualified_enrichment.records import digest
            receipt['review_packet_sha256'] = digest(details)
        save(absolute(args.receipt),receipt)
        print(json.dumps(receipt,ensure_ascii=False)); return exit_code
    except (ValueError,OSError,KeyError,TypeError,RuntimeError,ImportError) as exc:
        print(json.dumps(dict(status='hold',error_type=type(exc).__name__,diagnostic=str(exc)))); return 2


if __name__=='__main__': raise SystemExit(main())
