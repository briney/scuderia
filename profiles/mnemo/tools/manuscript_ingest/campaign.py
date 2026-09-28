"""Bounded paper campaign operations; scientific work belongs to manuscript_ingest."""
import argparse
import hashlib
import json
from pathlib import Path
import sys
import yaml

if not __package__:
    sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
    __package__='manuscript_ingest'
from . import workflow as w


def _scan(instance):
    instance=w.absolute(instance); items=[]; diagnostics=[]
    w.require((instance/'papers').is_dir(),'papers-directory-required')
    for path in sorted((instance/'papers').glob('*.md')):
        try:
            w.absolute(path); raw=path.read_bytes(); text=raw.decode('utf-8'); fm=w.page_metadata(text)
            w.require(fm.get('kind')=='paper','paper-kind-required')
            for key in ('tags','cited_by','links'):
                w.require(isinstance(fm.get(key) or [],list),'invalid-list:'+key)
            for key in ('needs-ingest','needs-enrichment'):
                w.require(fm.get(key) is None or type(fm[key]) is bool,'invalid-boolean:'+key)
            items.append(dict(path=str(path),sha256=hashlib.sha256(raw).hexdigest(),metadata=fm))
        except (OSError,ValueError,yaml.YAMLError) as exc:
            diagnostics.append(dict(path=str(path),reason=str(exc)))
    return dict(items=items,diagnostics=diagnostics)


def scan_queue(instance:Path)->dict:
    result=_scan(instance)
    result['items']=[r for r in result['items'] if r['metadata'].get('needs-ingest') is True]
    result['items'].sort(key=lambda r:(-len(r['metadata'].get('cited_by') or []),r['path']))
    return result


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    commands=parser.add_subparsers(dest='command',required=True)
    scan=commands.add_parser('scan-queue'); scan.add_argument('--instance',required=True,type=Path)
    scan.add_argument('--output',type=Path,help='New external JSON file; stdout otherwise')
    args=parser.parse_args(argv)
    try:
        result=scan_queue(args.instance)
        if args.output:
            from article_archive_compat.portable_articles import save
            save(w.outside_instance(args.output),result)
            result=dict(output=str(args.output),items=len(result['items']),diagnostics=len(result['diagnostics']))
        print(json.dumps(result,ensure_ascii=False));return 0
    except (OSError,ValueError,yaml.YAMLError) as exc:
        print(json.dumps(dict(error=str(exc))));return 2

if __name__=='__main__':raise SystemExit(main())
