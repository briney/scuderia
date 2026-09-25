"""Historical enrichment preparation/readers; live execution requires a current portable job."""
import argparse
import json
import os
from pathlib import Path
from .io import offline


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--offline',action='store_true')
    subs=parser.add_subparsers(dest='command',required=True)
    p=subs.add_parser('prepare')
    p.add_argument('--source-package',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    p.add_argument('--method',type=Path,default=os.environ.get('PDF_ENRICHMENT_METHOD'))
    p.add_argument('--kinds',default='figure,table,algorithm')
    p.add_argument('--element',action='append',dest='element_ids',help='Exact source element ID; repeat for bounded roster')
    p.add_argument('--caption-only',action='store_true')
    p.add_argument('--fixture',action='store_true',help='Permanently synthetic-only run')
    p=subs.add_parser('count'); p.add_argument('--run',type=Path,required=True); p.add_argument('--processor-cache',type=Path,required=True)
    p=subs.add_parser('seal'); p.add_argument('--run',type=Path,required=True)
    p=subs.add_parser('execute'); p.add_argument('--run',type=Path,required=True)
    p.add_argument('--approval',type=Path,required=True); p.add_argument('--authorize-posts',action='store_true')
    p=subs.add_parser('import-test-response'); p.add_argument('--run',type=Path,required=True)
    p.add_argument('--responses',type=Path,required=True); p.add_argument('--request')
    p=subs.add_parser('report'); p.add_argument('--run',type=Path,required=True); p.add_argument('--output',type=Path)
    args=parser.parse_args(argv)
    if args.offline or os.environ.get('PDF_ENRICHMENT_OFFLINE'): offline()
    from . import requests, importer, live
    try:
        if args.command=='prepare':
            result=requests.prepare(args.source_package,args.output,kinds=args.kinds.split(','),caption_only=args.caption_only,
                                    element_ids=args.element_ids,method=args.method,fixture=args.fixture)
            summary=dict(output=str(args.output),selected_requests=sum(bool(r.get('id')) for r in result['requests']),elements=len(result['requests']),documents=len(result['documents']))
        elif args.command=='count':
            result=live.count(args.run,args.processor_cache)
            summary=dict(counted=len(result['requests']),fits=sum(c['fits'] for c in result['requests'].values()))
        elif args.command=='seal':
            result=live.seal(args.run)
            summary=dict(approval_template=str(args.run/'approval.template.json'),approved=False,ready_requests=len(result['requests']))
        elif args.command=='execute':
            live.execute(args.run,args.approval,authorize=args.authorize_posts)
        elif args.command=='import-test-response':
            summary=dict(imported=importer.import_test_response(args.run,args.responses,args.request))
        else:
            result=importer.report(args.run,args.output)
            summary=dict(report=str((args.output or args.run)/'report.json'),review=str((args.output or args.run)/'review.html'),requested_work_complete=result['requested_work_complete'],production_complete=False)
        print(json.dumps(summary)); return 0
    except (ValueError,AssertionError,KeyError,TypeError,OSError,RuntimeError) as exc:
        print(json.dumps(dict(status='blocked',error_type=type(exc).__name__,diagnostic=str(exc)))); return 2


if __name__=='__main__': raise SystemExit(main())
