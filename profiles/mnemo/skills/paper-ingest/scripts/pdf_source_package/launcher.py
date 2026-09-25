"""Fixed-command workflow launcher. No transport, secrets or shell evaluation."""
from datetime import datetime, timezone
from dataclasses import dataclass
import argparse
import codecs
import json
import math
import os
from pathlib import Path
import selectors
import signal
import subprocess
import sys
import threading
import time
from typing import Any

from .io import load, save, safe, sha, require


def utc_now():
    return datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')


class LauncherSignal(BaseException):
    def __init__(self, number):
        self.number = number


def terminate_group(child, errors):
    """Kill descendants as well as the immediate child; always reap our child."""
    try:
        os.killpg(child.pid, signal.SIGTERM)
    except ProcessLookupError:
        pass
    except OSError as exc:
        errors.append(dict(action='group-SIGTERM', error_type=type(exc).__name__, errno=exc.errno))
    try:
        child.wait(timeout=1)
    except subprocess.TimeoutExpired:
        pass
    try:
        os.killpg(child.pid, signal.SIGKILL)
    except ProcessLookupError:
        pass
    except OSError as exc:
        # Retain group cleanup errors rather than dropping the child's exit.
        errors.append(dict(action='group-SIGKILL', error_type=type(exc).__name__, errno=exc.errno))
    if child.poll() is None:
        child.kill()
    return child.wait()


def run_child(argv, cwd, attempt_dir, timeout):
    """Internal process primitive, not a tool surface. argv is code-owned.

    process.json is pessimistic until reaping AND logging succeed. SIGKILL can
    leave a running record, never a successful one. Tool success is decided by
    launch() only after separate artifact verification.
    """
    attempt = Path(attempt_dir)
    attempt.mkdir(mode=0o700)
    record: dict[str, Any] = dict(schema='pdf-workflow-process-v1', started_at=utc_now(), ended_at=None,
                  argv=list(map(str, argv)), cwd=str(cwd), process_status='running',
                  exit_code=None, child_pid=None, termination=None, termination_errors=[], success=False,
                  artifact_status='not-checked', log=str(attempt / 'console.log'))
    save(attempt / 'process.json', record)
    child = None
    previous = {}
    def interrupted(number, frame):
        raise LauncherSignal(number)
    if threading.current_thread() is threading.main_thread():
        for number in (signal.SIGINT, signal.SIGTERM, signal.SIGHUP):
            previous[number] = signal.signal(number, interrupted)
    try:
        with (attempt / 'console.log').open('xb', buffering=0) as log:
            child = subprocess.Popen(list(map(str, argv)), cwd=str(cwd), shell=False,
                                     stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                     start_new_session=True)
            record['child_pid'] = child.pid
            save(attempt / 'process.json', record, replace=True)
            deadline = time.monotonic() + timeout
            decoder = codecs.getincrementaldecoder('utf-8')('replace')
            assert child.stdout is not None
            with selectors.DefaultSelector() as selector:
                selector.register(child.stdout, selectors.EVENT_READ)
                while selector.get_map():
                    left = deadline - time.monotonic()
                    if left <= 0:
                        raise subprocess.TimeoutExpired(argv, timeout)
                    for key, _ in selector.select(min(left, 0.1)):
                        data = os.read(key.fd, 65536)
                        if not data:
                            selector.unregister(key.fileobj)
                            continue
                        log.write(data)
                        os.fsync(log.fileno())
                        sys.stderr.write(decoder.decode(data))
                        sys.stderr.flush()
                sys.stderr.write(decoder.decode(b'', final=True))
                sys.stderr.flush()
            record['exit_code'] = child.wait(timeout=max(0.001, deadline - time.monotonic()))
            os.fsync(log.fileno())
            record['process_status'] = 'exited' if record['exit_code'] == 0 else 'failed'
            record['termination'] = 'child-signal' if record['exit_code'] < 0 else 'normal'
    except (subprocess.TimeoutExpired, LauncherSignal, KeyboardInterrupt) as exc:
        # Ignore further termination signals only during bounded cleanup.
        for number in previous:
            signal.signal(number, signal.SIG_IGN)
        record['termination'] = 'timeout' if isinstance(exc, subprocess.TimeoutExpired) else 'launcher-signal'
        if isinstance(exc, LauncherSignal):
            record['signal'] = exc.number
        record['process_status'] = 'failed'
        if child is not None:
            record['exit_code'] = terminate_group(child, record['termination_errors'])
    except Exception as exc:
        for number in previous:
            signal.signal(number, signal.SIG_IGN)
        record.update(process_status='failed', termination='launcher-error', error_type=type(exc).__name__)
        if child is not None:
            record['exit_code'] = terminate_group(child, record['termination_errors'])
    finally:
        if child is not None:
            if child.poll() is None:
                record['exit_code'] = terminate_group(child, record['termination_errors'])
                record.update(process_status='failed', termination='cleanup')
            if child.stdout is not None:
                child.stdout.close()
        for number, handler in previous.items():
            signal.signal(number, handler)
    record['ended_at'] = utc_now()
    # Failure to persist this record propagates; successful logging never masks
    # a child failure, and successful JSON writes never mask a logging failure.
    save(attempt / 'process.json', record, replace=True)
    return record


OPERATIONS = ('prepare', 'prepare-stage', 'count', 'seal', 'execute', 'replay', 'report', 'finalize', 'summary')
PHASES = ('initial', 'classification', 'association')
PATH_FLAGS = dict(package_dir='--root', output_dir='--output', scope_path='--scope',
                  approval_path='--approval', processor_cache='--processor-cache',
                  responses_path='--responses', inspection_dir='--inspections')
REQUIRED = {
    'prepare': {'scope_path', 'output_dir'},
    'prepare-stage': {'package_dir', 'phase'},
    'count': {'package_dir', 'phase', 'processor_cache'},
    'seal': {'package_dir', 'phase'},
    'execute': {'package_dir', 'phase', 'approval_path'},
    'replay': {'package_dir', 'phase', 'approval_path', 'responses_path'},
    'report': {'package_dir'}, 'finalize': {'package_dir'}, 'summary': {'package_dir', 'output_dir'},
}


@dataclass(frozen=True)
class Deployment:
    """Trusted operator configuration, never tool-call arguments."""
    method_dir: Path = Path(__file__).resolve().parent.parent
    python: Path = Path(sys.executable)

    def check(self):
        require(self.method_dir.is_absolute() and self.method_dir.is_dir(), 'trusted-method-directory-required')
        require((self.method_dir/'pdf_source_package/cli.py').is_file(), 'trusted-method-unavailable')
        require(self.python.is_absolute() and self.python.is_file() and os.access(self.python, os.X_OK), 'trusted-python-unavailable')


def absolute_path(value):
    require(isinstance(value, str) and bool(value) and '\x00' not in value, 'path-required')
    p = Path(value)
    require(p.is_absolute() and '..' not in p.parts and not any(x.is_symlink() for x in (p, *p.parents)), 'absolute-nonsymlink-path-required')
    return p


def validated(args):
    require(isinstance(args, dict), 'arguments-object-required')
    operation = args.get('operation')
    require(operation in OPERATIONS, 'unsupported-operation')
    required = REQUIRED[operation] | {'operation', 'attempt_dir'}
    allowed = required | {'offline', 'authorize_posts', 'timeout'}
    if operation == 'prepare': allowed.add('offline_fixture')
    if operation in ('report', 'finalize', 'summary'): allowed.add('inspection_dir')
    require(required <= args.keys() and args.keys() <= allowed, 'operation-arguments')
    value = dict(args)
    for flag in ('offline', 'authorize_posts', 'offline_fixture'):
        require(type(value.get(flag, False)) is bool, 'boolean-required:' + flag)
    timeout = value.get('timeout', 14400)
    require(type(timeout) in (int, float) and math.isfinite(timeout) and 0 < timeout <= 86400, 'timeout-range')
    value['timeout'] = timeout
    if 'phase' in value:
        require(value['phase'] in PHASES and not (operation == 'prepare-stage' and value['phase'] == 'initial'), 'operation-phase')
    authorize = value.get('authorize_posts', False)
    require(not authorize or operation == 'execute', 'authorization-only-for-execute')
    if operation == 'execute':
        require(authorize is True and not value.get('offline', False), 'explicit-live-authorization-required')
    if operation == 'replay': value['offline'] = True
    require(not value.get('offline_fixture') or value.get('offline'), 'offline-fixture-requires-offline')
    paths = {k:absolute_path(v) for k,v in value.items() if k in PATH_FLAGS or k == 'attempt_dir'}
    attempt = paths['attempt_dir']
    require(not attempt.exists() and attempt.parent.is_dir(), 'attempt-directory-must-be-new-with-existing-parent')
    root = paths.get('package_dir', paths.get('output_dir'))
    require(not attempt.is_relative_to(root) and not root.is_relative_to(attempt), 'attempt-directory-must-be-external')
    for key, p in paths.items():
        if key in ('attempt_dir','output_dir','inspection_dir'): continue
        require(p.exists(), 'input-path-unavailable:' + key)
        if key in ('package_dir','processor_cache'): require(p.is_dir(), 'directory-required:' + key)
        else: require(p.is_file(), 'file-required:' + key)
    if 'output_dir' in paths:
        output = paths['output_dir']
        require(not output.exists() and output.parent.is_dir(), 'output-must-be-new-with-existing-parent')
        require(not output.is_relative_to(attempt) and not attempt.is_relative_to(output), 'output-attempt-overlap')
        if operation == 'summary':
            require(not output.is_relative_to(root), 'summary-output-must-be-external')
    if operation == 'prepare':
        for doc in load(paths['scope_path'])['documents']:
            require(absolute_path(doc['source']).is_file(), 'absolute-source-file-required')
    for key, p in paths.items(): value[key] = str(p)
    return value


def launch(args, deployment=None):
    """Library/tool entry: one validated public operation, no automatic retry."""
    args = validated(args)
    deployment = deployment or Deployment()
    deployment.check()
    attempt = Path(args['attempt_dir'])
    receipt_path = attempt/'phase-evidence.json'
    argv = [str(deployment.python), '-B', '-u', '-E', '-m', 'pdf_source_package']
    if args.get('offline'): argv.append('--offline')
    argv += ['--workflow-evidence', str(receipt_path), args['operation']]
    for key, flag in PATH_FLAGS.items():
        if key in args: argv += [flag, args[key]]
    if 'phase' in args: argv += ['--phase', args['phase']]
    if args.get('authorize_posts'): argv.append('--authorize-posts')
    if args.get('offline_fixture'): argv.append('--offline-fixture')
    process = run_child(argv, deployment.method_dir, attempt, args['timeout'])
    result = dict(process, operation=args['operation'], phase=args.get('phase'), attempt_dir=str(attempt),
                  process_record=str(attempt/'process.json'), artifact_status='missing-or-invalid',
                  success=False, requested_work_complete=None)
    try:
        receipt = load(receipt_path)
        root = args.get('package_dir', args.get('output_dir'))
        require(receipt['schema'] == 'pdf-workflow-evidence-v1' and receipt['operation'] == args['operation'] and
                receipt['phase'] == args.get('phase') and receipt['package_dir'] == root, 'receipt-operation-binding')
        require(receipt['evidence_roots'] and any(receipt['evidence_roots'].values()), 'empty-operation-evidence')
        for evidence_root, bindings in receipt['evidence_roots'].items():
            require(evidence_root in (root, args.get('output_dir')), 'unexpected-evidence-root')
            for name, expected in bindings.items():
                require(sha(safe(evidence_root, name)) == expected, 'operation-artifact-changed')
        for key in ('artifact_status','phase_status','fixture','requested_work_complete','facts_path','summary_path','results_path'):
            if key in receipt: result[key] = receipt[key]
        if args['operation'] in ('report', 'finalize', 'summary'):
            destination = args.get('output_dir', root)
            summary_path = safe(destination, 'summary.txt')
            # Return the same verified projection as the export, not a second
            # summary supplied by a receipt or generated by a calling model.
            text = summary_path.read_text()
            require(sha(summary_path) == receipt['evidence_roots'][destination]['summary.txt'], 'summary-artifact-changed')
            result['summary'] = text
        result['phase_evidence'] = str(receipt_path)
        result['success'] = (process['process_status'] == 'exited' and process['exit_code'] == 0 and
                             receipt['artifact_status'] == 'verified' and
                             (args['operation'] != 'finalize' or receipt['requested_work_complete'] is True))
    except (OSError, ValueError, KeyError, TypeError) as exc:
        result['artifact_error_type'] = type(exc).__name__
    save(attempt/'result.json', result)
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('operation', choices=OPERATIONS)
    parser.add_argument('--attempt-dir', required=True)
    for name in PATH_FLAGS: parser.add_argument('--' + name.replace('_','-'))
    parser.add_argument('--phase', choices=PHASES)
    parser.add_argument('--timeout', type=float, default=14400)
    for name in ('offline', 'authorize-posts', 'offline-fixture'):
        parser.add_argument('--' + name, action='store_true', default=None)
    args = {k:v for k,v in vars(parser.parse_args(argv)).items() if v is not None}
    try:
        result = launch(args)
        print(json.dumps(result, allow_nan=False))
        return 0 if result['success'] else 1
    except (ValueError, OSError, KeyError, TypeError) as exc:
        print(json.dumps(dict(success=False, status='blocked', error_type=type(exc).__name__, diagnostic=str(exc))))
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
