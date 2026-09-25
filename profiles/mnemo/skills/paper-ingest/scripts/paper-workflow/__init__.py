"""Native Hermes directory plugin: one thin, fixed-argv workflow tool."""
import hashlib
import importlib
import importlib.util
import json
from pathlib import Path
import sys

PATHS = ('package_dir', 'output_dir', 'scope_path', 'approval_path', 'processor_cache',
         'responses_path', 'inspection_dir', 'attempt_dir')
SCHEMA = {
    'name': 'paper_workflow',
    'description': (
        'Run one public PDF source-package operation through its trusted CLI. '
        'All paths must be absolute. attempt_dir must be NEW with parents created safely, outside the package. '
        'prepare also needs scope_path/output_dir; prepare-stage needs phase; count needs phase/processor_cache; '
        'seal needs phase; execute needs phase/approval_path AND explicit authorize_posts=true; '
        'replay needs phase/approval_path/responses_path and an offline fixture. '
        'report/finalize refresh package review; summary writes read-only facts to a NEW external output_dir. '
        'Optional inspection_dir checks exact image-input provenance, not human acceptance. '
        'No retries/resume, next-phase approval, acquisition, arbitrary commands or model changes. '
        'prepare with processor_cache also counts and seals; seal with processor_cache resumes offline bookkeeping. Returns actual child exit, process/artifact status, tool success, durable logs and report paths. '
        'timeout is the launcher wall-clock bound; application request timeout remains 1200 seconds.'
    ),
    'parameters': {
        'type': 'object', 'additionalProperties': False,
        'properties': {
            'operation': {'type': 'string', 'enum': ['prepare','prepare-stage','count','seal','execute','replay','report','finalize','summary']},
            'phase': {'type': 'string', 'enum': ['initial','classification','association']},
            **{name: {'type':'string','minLength':1,'maxLength':4096} for name in PATHS},
            'authorize_posts': {'type':'boolean','default':False},
            'offline': {'type':'boolean','default':False},
            'offline_fixture': {'type':'boolean','default':False},
            'timeout': {'type':'number','exclusiveMinimum':0,'maximum':86400,'default':14400},
        },
        'required': ['operation','attempt_dir'],
    },
}


def runner(method_dir):
    """Load only the configured method, not PYTHONPATH or a caller-selected file."""
    root = Path(method_dir)
    if not root.is_absolute() or not (root/'pdf_source_package/__init__.py').is_file():
        raise ValueError('trusted-method-unavailable')
    name = '_paper_workflow_method_' + hashlib.sha256(str(root).encode()).hexdigest()[:16]
    if name not in sys.modules:
        spec = importlib.util.spec_from_file_location(name, root/'pdf_source_package/__init__.py',
                                                     submodule_search_locations=[str(root/'pdf_source_package')])
        module = importlib.util.module_from_spec(spec)
        sys.modules[name] = module
        spec.loader.exec_module(module)
    return importlib.import_module(name + '.launcher')


def register(ctx):
    # Native plugin settings only. Registration never reads credential files,
    # creates a subprocess, imports PDF/model dependencies, or contacts a route.
    method_dir = ctx.get_config('method_dir', None)
    python = ctx.get_config('python', None)

    def available():
        return (isinstance(method_dir, str) and Path(method_dir).is_absolute() and
                (Path(method_dir)/'pdf_source_package/launcher.py').is_file() and
                isinstance(python, str) and Path(python).is_absolute() and Path(python).is_file())

    def dispatch(args, **kwargs):
        try:
            if not available(): raise ValueError('configure-trusted-method-dir-and-python')
            module = runner(method_dir)
            value = module.launch(args, module.Deployment(Path(method_dir), Path(python)))
            return json.dumps(value, allow_nan=False)
        except Exception as exc:
            # Any evidence/logging failure is a failure, never a success fallback.
            return json.dumps(dict(success=False, status='blocked-or-launcher-failed', error_type=type(exc).__name__,
                                   diagnostic=str(exc) if isinstance(exc, ValueError) else 'Inspect the new attempt directory, if created.'))

    ctx.register_tool(name='paper_workflow', toolset='paper_workflow', schema=SCHEMA,
                      handler=dispatch, check_fn=available)
