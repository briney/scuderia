"""Native Hermes capability; registration is read-only and inference-free."""
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

SETTINGS=('integration_dir','enrichment_root','method_dir','adapter_dir','python')
PATHS=('source_handoff','output','test_root','job','processor_cache','approval','responses',
       'run','review_root','packet','submission','export_path','source_inspection','attempt_dir')
SCHEMA=dict(name='paper_enrichment',description=(
    'Run one qualified figure/table enrichment or contextual review operation. Trusted deployment paths are configured, not caller arguments. '
    'New preparation selects all eligible figures/tables; algorithms remain deferred. Preparation/review are offline. '
    'execute needs a separately authored approval and authorize_posts=true; local failures continue independent requests; explicit continuation sends only never-reserved siblings under identical approval/original budget. '
    'attempt_dir is new, external, with parents created safely. export retains actual request accounting; source-backed partial evidence may be page-ready. '
    'Record only observed substantive limitations; empty qualifications are valid. Specialized exact use needs source inspection or qualification; algorithm-specification always needs inspection. '
    'prepare with processor_cache also counts and seals; seal with processor_cache resumes offline bookkeeping. Returns actual child exit and hash-checked artifact receipt, not a scientific correctness claim.'),
    parameters=dict(type='object',additionalProperties=False,required=['operation','attempt_dir'],properties={
        'operation':dict(type='string',enum=['prepare','count','seal','execute','report','import-test-response','review-create','review-packet','review-import','export','verify-export','consume']),
        **{k:dict(type='string',minLength=1,maxLength=4096) for k in PATHS},
        'elements':dict(type='array',items=dict(type='string'),minItems=0,uniqueItems=True),
        'aspects':dict(type='array',items=dict(type='string',enum=['content','source-association','notation','layout','units','headers']),minItems=1,uniqueItems=True),
        'element':dict(type='string'),'target':dict(type='string'),
        'purpose':dict(type='string',enum=['discovery','summary','exact','algorithm-specification']),
        'qualification':dict(type='string'), 'kind':dict(type='string',enum=['qualified-job','v7-run']),
        'max_bytes':dict(type='integer',minimum=1024,maximum=8000000),
        'authorize_posts':dict(type='boolean',default=False),'offline':dict(type='boolean',default=False),
        'timeout':dict(type='number',exclusiveMinimum=0,maximum=86400,default=14400),
    }))


def runner(root):
    path=Path(root)/'qualified_enrichment/launcher.py'
    name='_paper_enrichment_launcher_'+hashlib.sha256(str(path).encode()).hexdigest()[:16]
    if name not in sys.modules:
        spec=importlib.util.spec_from_file_location(name,path)
        module=importlib.util.module_from_spec(spec); sys.modules[name]=module; spec.loader.exec_module(module)
    return sys.modules[name]


def register(ctx):
    config={key:ctx.get_config(key,None) for key in SETTINGS}
    def available():
        return (all(isinstance(v,str) and Path(v).is_absolute() for v in config.values()) and
                (Path(config['integration_dir'])/'qualified_enrichment/launcher.py').is_file() and
                (Path(config['enrichment_root'])/'pdf_enrichment/live.py').is_file() and
                (Path(config['method_dir'])/'pdf_source_package/phase_evidence.py').is_file() and
                (Path(config['adapter_dir'])/'source_package.py').is_file() and Path(config['python']).is_file())
    def dispatch(args,**kwargs):
        try:
            if not available(): raise ValueError('configure-all-trusted-deployment-inputs')
            module=runner(config['integration_dir'])
            result=module.launch(args,module.Deployment(**{k:Path(v) for k,v in config.items()}))
            return json.dumps(result,allow_nan=False)
        except Exception as exc:
            return json.dumps(dict(success=False,status='blocked-or-launcher-failed',error_type=type(exc).__name__,
                                   diagnostic=str(exc) if isinstance(exc,ValueError) else 'Inspect the new attempt directory if created.'))
    ctx.register_tool(name='paper_enrichment',toolset='paper_enrichment',schema=SCHEMA,handler=dispatch,check_fn=available)
