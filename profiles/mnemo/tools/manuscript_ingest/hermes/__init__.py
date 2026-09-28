"""Thin Hermes binding. Runtime/configuration roots come only from deployment."""
import json
import os
from pathlib import Path
import subprocess

SCHEMA=dict(name='paper_ingest',description='Ingest or refresh a paper from its manuscript. Retain sources, read manuscript evidence, stage a focused source-reviewed page, then publish. Use the returned job_id across interruptions and revisions. Supplementary files are stored without processing. Tool configuration owns paths, accounting, and provenance.',
    parameters=dict(type='object',additionalProperties=False,required=['operation'],properties={
        'operation':dict(type='string',enum=['start','sources','read','stage','publish','status']),
        'page':dict(type='string',description='Existing or new absolute paper page; start only.'),
        'identity':dict(type='object',description='Resolved article title, DOI/PMID and version; cannot contradict the current page.'),
        'job_id':dict(type='string'),
        'inputs':dict(type='array',description='Acquired inputs with path, role manuscript/body/supplement, identity and source-backed basis for manuscript/body. Omit to reuse the existing archive.',items=dict(type='object')),
        'locations':dict(type='array',minItems=1,maxItems=8,items=dict(type='object',additionalProperties=False,required=['source_id','page'],properties={
            'source_id':dict(type='string'),'page':dict(type='integer',minimum=1),'start_char':dict(type='integer',minimum=0),'max_chars':dict(type='integer',minimum=1,maximum=32000)})),
        'question':dict(type='string',description='Optional specific manuscript inspection question, up to four explicit pages; consumes configured inspection budget.'),
        'markdown':dict(type='string',description='Full candidate page; stage never changes the live page.'),
        'review_note':dict(type='string',description='Short source check of central findings, consequential numbers, contradictions and material omissions. Use HOLD: on a line for each unresolved material issue; omit HOLD lines when none remain. Optional missing output alone does not block.'),
        'revision':dict(type='integer',minimum=1),
    }))


def register(ctx):
    config={key:ctx.get_config(key,None) for key in ('tools_root','runtime_root','python')}
    def available():
        return all(isinstance(v,str) and Path(v).is_absolute() for v in config.values()) and (Path(config['tools_root'])/'manuscript_ingest/cli.py').is_file() and (Path(config['runtime_root'])/'config.json').is_file() and Path(config['python']).is_file()
    def handle(args,**kwargs):
        if not available():return json.dumps(dict(job_id=None,status='held',next_action='Configure the manuscript ingestion runtime.',artifacts={},warnings=[],blocking_reason='deployment-unavailable'))
        env=dict(os.environ,PYTHONPATH=config['tools_root'],PYTHONDONTWRITEBYTECODE='1')
        try:
            result=subprocess.run([config['python'],'-B','-m','manuscript_ingest.cli','--runtime-root',config['runtime_root']],
                input=json.dumps(args,allow_nan=False),text=True,capture_output=True,env=env,timeout=900)
            return json.dumps(json.loads(result.stdout))
        except (OSError,ValueError,subprocess.TimeoutExpired):
            return json.dumps(dict(job_id=args.get('job_id'),status='held',next_action='Check status with the same job_id; any reserved request will not repeat.',artifacts={},warnings=[],blocking_reason='runtime-interrupted-or-invalid-output'))
    ctx.register_tool(name='paper_ingest',toolset='paper_ingest',schema=SCHEMA,handler=handle,check_fn=available)
