"""Offline subprocess controls; no application transport or approvals."""
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import tempfile
import threading
import unittest
from unittest.mock import patch


class ProcessTests(unittest.TestCase):
    def test_launcher_sigterm_reaps_child_and_retains_signal(self):
        from pdf_source_package.launcher import run_child
        with tempfile.TemporaryDirectory(dir=os.environ.get('PDF_TEST_WORK') or os.environ['TMPDIR']) as tmp:
            root = Path(tmp)
            timer = threading.Timer(0.2, lambda: os.kill(os.getpid(), signal.SIGTERM))
            timer.start()
            try:
                result = run_child([sys.executable,'-B','-c','import time; time.sleep(30)'], root, root/'attempt', 5)
            finally:
                timer.cancel(); timer.join()
            self.assertEqual(result['termination'], 'launcher-signal')
            self.assertEqual(result['signal'], signal.SIGTERM)
            self.assertIs(type(result['exit_code']), int)
            self.assertFalse(result['success'])
            with self.assertRaises(ProcessLookupError): os.kill(result['child_pid'], 0)

    def test_durable_log_failure_is_not_hidden_by_result_writes(self):
        from pdf_source_package.launcher import run_child
        with tempfile.TemporaryDirectory(dir=os.environ.get('PDF_TEST_WORK') or os.environ['TMPDIR']) as tmp:
            root = Path(tmp); real = os.fsync
            def fail_log(fd):
                log = root/'attempt/console.log'
                if log.exists() and os.fstat(fd).st_ino == log.stat().st_ino:
                    raise OSError('offline injected log fsync failure')
                return real(fd)
            with patch('pdf_source_package.launcher.os.fsync', side_effect=fail_log):
                result = run_child([sys.executable,'-B','-c','print("durability failure fixture")'], root, root/'attempt', 5)
            self.assertEqual(result['process_status'], 'failed')
            self.assertFalse(result['success'])
            self.assertIs(type(result['exit_code']), int)
            self.assertEqual(json.loads((root/'attempt/process.json').read_text())['termination'], 'launcher-error')

    def test_console_logging_failure_is_failure_even_if_json_writes_succeed(self):
        from pdf_source_package.launcher import run_child
        with tempfile.TemporaryDirectory(dir=os.environ.get('PDF_TEST_WORK') or os.environ['TMPDIR']) as tmp:
            root = Path(tmp)
            with patch.object(sys.stderr, 'write', side_effect=OSError('offline injected console failure')):
                result = run_child([sys.executable, '-B', '-c', 'print("log failure fixture")'], root, root/'attempt', 5)
            self.assertFalse(result['success'])
            self.assertEqual(result['process_status'], 'failed')
            self.assertEqual(result['termination'], 'launcher-error')
            self.assertIs(type(result['exit_code']), int)
            self.assertEqual(json.loads((root/'attempt/process.json').read_text())['process_status'], 'failed')

    def test_timeout_terminates_group_even_when_child_exits_first(self):
        from pdf_source_package.launcher import run_child
        with tempfile.TemporaryDirectory(dir=os.environ.get('PDF_TEST_WORK') or os.environ['TMPDIR']) as tmp:
            root = Path(tmp)
            # A child exiting zero must not hide a still-running descendant that
            # inherited the pipe. Descendant writes only inside the test scratch.
            script = ('import subprocess,sys; p=subprocess.Popen([sys.executable,"-c","import time; time.sleep(30)"]); '
                      'print(p.pid,flush=True)')
            result = run_child([sys.executable,'-B','-c',script], root, root/'attempt', 0.3)
            self.assertEqual(result['exit_code'], 0)
            self.assertEqual(result['termination'], 'timeout')
            self.assertEqual(result['process_status'], 'failed')
            pid = int((root/'attempt/console.log').read_text().strip())
            check = subprocess.run(['ps','-o','stat=','-p',str(pid)], capture_output=True, text=True)
            self.assertTrue(check.returncode == 1 or check.stdout.strip().startswith('Z'), check.stdout)

    def test_failure_exit_survives_successful_logging(self):
        from pdf_source_package.launcher import run_child
        with tempfile.TemporaryDirectory(dir=os.environ.get('PDF_TEST_WORK') or os.environ['TMPDIR']) as tmp:
            root = Path(tmp)
            result = run_child([sys.executable, '-B', '-c', 'print("offline child"); raise SystemExit(7)'],
                               root, root / 'attempt', 5)
            self.assertEqual(result['exit_code'], 7)
            self.assertEqual(result['process_status'], 'failed')
            self.assertFalse(result['success'])
            self.assertEqual(json.loads((root / 'attempt/process.json').read_text())['exit_code'], 7)
            self.assertIn('offline child', (root / 'attempt/console.log').read_text())
            self.assertTrue(result['started_at'].endswith('Z'))
            self.assertTrue(result['ended_at'].endswith('Z'))
            with self.assertRaises(FileExistsError):
                run_child([sys.executable, '-c', 'pass'], root, root / 'attempt', 5)

    def test_timeout_reaps_child_and_records_integer_exit(self):
        from pdf_source_package.launcher import run_child
        with tempfile.TemporaryDirectory(dir=os.environ.get('PDF_TEST_WORK') or os.environ['TMPDIR']) as tmp:
            root = Path(tmp)
            result = run_child([sys.executable, '-B', '-c', 'import time; print("offline sleep",flush=True); time.sleep(30)'],
                               root, root / 'attempt', 0.2)
            self.assertIs(type(result['exit_code']), int)
            self.assertEqual(result['termination'], 'timeout')
            self.assertFalse(result['success'])
            with self.assertRaises(ProcessLookupError):
                os.kill(result['child_pid'], 0)

    def test_child_signal_is_not_success(self):
        from pdf_source_package.launcher import run_child
        with tempfile.TemporaryDirectory(dir=os.environ.get('PDF_TEST_WORK') or os.environ['TMPDIR']) as tmp:
            root = Path(tmp)
            result = run_child([sys.executable, '-B', '-c', 'import os,signal; os.kill(os.getpid(), signal.SIGTERM)'],
                               root, root / 'attempt', 5)
            self.assertEqual(result['exit_code'], -signal.SIGTERM)
            self.assertEqual(result['termination'], 'child-signal')
            self.assertFalse(result['success'])
