#!/usr/bin/env python3
"""Operator CLI using explicit trusted deployment and one fixed tool argument object."""
import argparse
import json
from pathlib import Path
import sys
from qualified_enrichment.launcher import Deployment, launch


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--deployment',type=Path,required=True)
    parser.add_argument('--arguments',type=Path,required=True)
    args=parser.parse_args()
    try:
        config=json.loads(args.deployment.read_bytes())
        if set(config)!=set(Deployment.__dataclass_fields__): raise ValueError('deployment-fields')
        deployment=Deployment(**{k:Path(v) for k,v in config.items()})
        if deployment.integration_dir != Path(__file__).resolve().parent: raise ValueError('operator-entry-deployment-mismatch')
        result=launch(json.loads(args.arguments.read_bytes()),deployment)
        print(json.dumps(result,indent=2)); return 0 if result['success'] else 1
    except (ValueError,KeyError,TypeError,OSError) as exc:
        print(json.dumps(dict(success=False,status='blocked',diagnostic=str(exc)))); return 2


if __name__=='__main__': raise SystemExit(main())
