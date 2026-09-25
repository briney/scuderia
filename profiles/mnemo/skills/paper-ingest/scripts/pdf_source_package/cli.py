"""One public CLI; offline stages never instantiate a transport."""
import argparse
import json
from pathlib import Path
from .io import offline


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--offline',action='store_true',help='Block all socket operations in this process')
    parser.add_argument('--workflow-evidence',type=Path,help=argparse.SUPPRESS)
    subs=parser.add_subparsers(dest='command',required=True)
    p=subs.add_parser('prepare');p.add_argument('--scope',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--offline-fixture',action='store_true');p.add_argument('--processor-cache',type=Path)
    p=subs.add_parser('prepare-stage');p.add_argument('--root',type=Path,required=True);p.add_argument('--phase',choices=['classification','association'],required=True);p.add_argument('--processor-cache',type=Path)
    p=subs.add_parser('count');p.add_argument('--root',type=Path,required=True);p.add_argument('--phase',choices=['initial','classification','association'],required=True);p.add_argument('--processor-cache',type=Path,required=True)
    p=subs.add_parser('seal');p.add_argument('--root',type=Path,required=True);p.add_argument('--phase',choices=['initial','classification','association'],required=True);p.add_argument('--processor-cache',type=Path)
    p=subs.add_parser('execute');p.add_argument('--root',type=Path,required=True);p.add_argument('--phase',choices=['initial','classification','association'],required=True);p.add_argument('--approval',type=Path,required=True);p.add_argument('--authorize-posts',action='store_true')
    p=subs.add_parser('replay');p.add_argument('--root',type=Path,required=True);p.add_argument('--phase',choices=['initial','classification','association'],required=True);p.add_argument('--approval',type=Path,required=True);p.add_argument('--responses',type=Path,required=True)
    for name in ('report','finalize'):
        p=subs.add_parser(name);p.add_argument('--root',type=Path,required=True);p.add_argument('--inspections',type=Path)
    p=subs.add_parser('summary');p.add_argument('--root',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--inspections',type=Path)
    args=parser.parse_args(argv)
    if args.offline or args.command=='replay': offline()
    from . import preparation, workflow, gates, execution, review
    try:
        exit_code = 0
        state = None
        if args.command=='prepare':
            result=preparation.prepare(args.scope,args.output,args.offline_fixture)
            print(json.dumps(dict(documents=len(result['documents']),output=str(args.output))))
        elif args.command=='prepare-stage':
            result=workflow.prepare_stage(args.root,args.phase);print(json.dumps(dict(requests=len(result['requests']))))
        elif args.command=='count': gates.count_phase(args.root,args.phase,args.processor_cache)
        elif args.command=='seal':
            gates.prepare_phase(args.root,args.phase,args.processor_cache)
        elif args.command in ('execute','replay'):
            exit_code = execution.run_phase(args.root,args.phase,args.approval,
                authorize=getattr(args,'authorize_posts',False),replay=getattr(args,'responses',None))
        elif args.command == 'summary':
            state = review.export_summary(args.root,args.output,args.inspections)
            print(json.dumps(dict(requested_work_complete=state['requested_work_complete'],human_acceptance='pending',facts=str(args.output/'facts.json'),summary=str(args.output/'summary.txt'))))
        else:
            result=review.report(args.root,args.inspections)
            state = result
            print(json.dumps(dict(requested_work_complete=result['requested_work_complete'],human_acceptance='pending')))
            exit_code = 0 if result['requested_work_complete'] else 1
        if args.command in ('prepare','prepare-stage'):
            root = args.output if args.command == 'prepare' else args.root
            phase = 'initial' if args.command == 'prepare' else args.phase
            from .io import load
            if args.processor_cache or not load(root/f'{phase}-plan.json')['requests']:
                gates.prepare_phase(root,phase,args.processor_cache)
        if args.workflow_evidence:
            from .phase_evidence import operation_evidence
            from .io import save
            receipt = operation_evidence(args.output if args.command == 'prepare' else args.root,
                args.command,getattr(args,'phase',None),getattr(args,'output',None),state)
            save(args.workflow_evidence,receipt)
        return exit_code
    except (ValueError,AssertionError,OSError,KeyError,TypeError) as exc:
        if args.command == 'count':
            from .io import save
            failure = dict(phase=args.phase, status='count-stage-failed', error_type=type(exc).__name__, diagnostic=str(exc), application_posts=0)
            if args.root.exists():
                for name in (f'{args.phase}-count-failure.json', 'stop.json'):
                    if not (args.root / name).exists():
                        save(args.root / name, failure)
        # Never print arbitrary transport exception strings or credentials.
        print(json.dumps(dict(status='blocked',error_type=type(exc).__name__,diagnostic=str(exc) if args.command!='execute' else 'Inspect retained request evidence; do not retry uncertain attempts.')))
        return 2
