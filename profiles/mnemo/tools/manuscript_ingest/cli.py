"""Fixed operations shared by the CLI and native tool; no nested dispatcher."""
import argparse
import json
from pathlib import Path
import sys
from . import workflow as w, sources

OPERATIONS={
    'start':({'page'},{'identity'}),
    'sources':({'job_id'},{'inputs'}),
    'read':({'job_id','locations'},{'question','transcribe'}),
    'stage':({'job_id','markdown','review_note'},{'base_revision'}),
    'publish':({'job_id','revision'},set()),
    'status':({'job_id'},set()),
}


def dispatch(arguments,*,runtime_root):
    w.require(isinstance(arguments,dict),'operation-object-required')
    operation=arguments.get('operation'); w.require(operation in OPERATIONS,'unknown-operation')
    required,optional=OPERATIONS[operation]; keys=set(arguments)-{'operation'}
    w.require(required<=keys and keys<=required|optional,'operation-arguments-mismatch')
    args={k:v for k,v in arguments.items() if k!='operation'}
    function={'sources':sources.prepare,'read':sources.read}.get(operation) or getattr(w,operation)
    return function(**args,runtime_root=runtime_root)


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--runtime-root',required=True,type=Path)
    parser.add_argument('--input',type=Path,help='JSON operation file; stdin if omitted')
    args=parser.parse_args(argv)
    try:
        raw=args.input.read_text() if args.input else sys.stdin.read(2_000_001)
        w.require(len(raw)<=2_000_000,'operation-input-too-large')
        result=dispatch(json.loads(raw),runtime_root=args.runtime_root)
        print(json.dumps(result,ensure_ascii=False,allow_nan=False)); return 0
    except (ValueError,OSError,KeyError,TypeError) as exc:
        print(json.dumps(dict(job_id=None,status='held',next_action='Correct the named input or configuration; do not restart paid work.',artifacts={},warnings=[],blocking_reason=str(exc)),ensure_ascii=False)); return 2

if __name__=='__main__':raise SystemExit(main())
