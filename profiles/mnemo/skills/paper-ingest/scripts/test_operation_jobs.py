"""Detached operation tests use real subprocesses and synthetic source PDFs."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import unittest


class JobTests(unittest.TestCase):
    def test_fresh_caller_collects_same_attempt_without_redispatch(self):
        import operation_jobs as jobs
        import pymupdf
        from pdf_source_package.launcher import Deployment
        from pdf_source_package.io import sha
        with tempfile.TemporaryDirectory(dir=os.environ['SOURCE_PACKAGE_TEST_ROOT']) as tmp:
            root=Path(tmp); pdf=root/'source.pdf'
            with pymupdf.open() as doc:
                doc.new_page().insert_text((40,40),'Synthetic deployment check'); doc.save(pdf)
            scope=root/'scope.json'; scope.write_text(json.dumps(dict(application_endpoint='https://example.invalid/v1/chat/completions',
                max_application_posts=4,documents=[dict(identity='synthetic',source=str(pdf),sha256=sha(pdf),channels=['caption'])])))
            scripts=Path(jobs.__file__).parent; deployment=Deployment(scripts,Path(sys.executable))
            args=dict(operation='prepare',scope_path=str(scope),output_dir=str(root/'package'),
                      offline=True,offline_fixture=True,attempt_dir=str(root/'attempt'))
            started=jobs.start('source',args,deployment)
            self.assertEqual(started['attempt_dir'],str(root/'attempt'))
            again=jobs.start('source',args,deployment)
            self.assertEqual(again['job_sha256'],started['job_sha256'])
            deadline=time.monotonic()+15
            while time.monotonic()<deadline:
                result=jobs.status(root/'attempt')
                if result['status'] in ('finished','failed','uncertain'): break
                time.sleep(.05)
            self.assertEqual(result['status'],'finished',result)
            self.assertTrue(result['result']['success'])
            check=subprocess.run([sys.executable,'-B',str(scripts/'operation_jobs.py'),'status',str(root/'attempt')],capture_output=True,text=True)
            self.assertEqual(check.returncode,0,check.stderr)
            self.assertEqual(json.loads(check.stdout)['result'],result['result'])
            self.assertEqual(len(list((root/'attempt').glob('worker'))),1)
            (root/'package/manifest.json').write_text('{}')
            with self.assertRaisesRegex(ValueError,'terminal-artifact-changed'): jobs.status(root/'attempt')
            changed=dict(args,output_dir=str(root/'different'))
            with self.assertRaisesRegex(ValueError,'different-operation'): jobs.start('source',changed,deployment)

    def test_missing_terminal_receipt_never_claims_success(self):
        import operation_jobs as jobs
        with tempfile.TemporaryDirectory(dir=os.environ['SOURCE_PACKAGE_TEST_ROOT']) as tmp:
            root=Path(tmp)
            with self.assertRaises(ValueError): jobs.status(root)

    def test_crashed_supervisor_is_uncertain_and_cancel_does_not_redispatch(self):
        import operation_jobs as jobs
        from article_runtime import sha
        with tempfile.TemporaryDirectory(dir=os.environ['SOURCE_PACKAGE_TEST_ROOT']) as tmp:
            root=Path(tmp)
            jobs.write(root/'job.json',dict(schema='paper-operation-job-v1',created_at=0,identity={}))
            (root/'job.sha256').write_text(sha(root/'job.json'))
            result=jobs.status(root)
            self.assertEqual(result['status'],'uncertain'); self.assertFalse(result['success'])
            cancelled=jobs.cancel(root)
            self.assertTrue(cancelled['cancellation_requested'])
            self.assertFalse((root/'worker').exists())

    def test_cancellation_before_dispatch_has_terminal_failure(self):
        import operation_jobs as jobs
        from article_runtime import sha
        with tempfile.TemporaryDirectory(dir=os.environ['SOURCE_PACKAGE_TEST_ROOT']) as tmp:
            root=Path(tmp)
            jobs.write(root/'job.json',dict(schema='paper-operation-job-v1',created_at=0,
                identity=dict(kind='source',arguments={},deployment={}),supervisor_sha256=sha(Path(jobs.__file__).resolve())))
            (root/'job.sha256').write_text(sha(root/'job.json'))
            jobs.cancel(root)
            worker=subprocess.run([sys.executable,'-B',jobs.__file__,'worker',str(root),sha(root/'job.json')],capture_output=True,text=True)
            self.assertEqual(worker.returncode,0,worker.stderr)
            result=jobs.status(root)
            self.assertEqual(result['status'],'failed')
            self.assertEqual(result['result']['diagnostic'],'cancelled-before-dispatch')

    def test_native_enrichment_background_reattaches(self):
        import operation_jobs as jobs
        from qualified_enrichment.launcher import Deployment,launch
        scripts=Path(jobs.__file__).parent
        with tempfile.TemporaryDirectory(dir=os.environ['SOURCE_PACKAGE_TEST_ROOT']) as tmp:
            root=Path(tmp); page=root/'page.md'; page.write_text('---\nkind: paper\nslug: synthetic\n---\n# Synthetic\n')
            args=dict(operation='article',arguments=dict(command='route',article='synthetic',page=str(page),work_root=str(root/'work')),
                      background=True,attempt_dir=str(root/'attempt'),offline=True)
            deployment=Deployment(scripts,scripts,scripts,scripts,Path(sys.executable))
            started=launch(args,deployment)
            deadline=time.monotonic()+10
            while time.monotonic()<deadline:
                result=launch(dict(operation='status',attempt_dir=str(root/'attempt')),deployment)
                if result['status'] in ('finished','failed'): break
                time.sleep(.05)
            self.assertEqual(result['status'],'finished',result)
            self.assertEqual(launch(args,deployment)['job_sha256'],started['job_sha256'])

    def test_installed_plugin_job_control_without_preloaded_script_path(self):
        scripts=Path(__file__).parent
        with tempfile.TemporaryDirectory(dir=os.environ['SOURCE_PACKAGE_TEST_ROOT']) as tmp:
            for plugin in ('paper-workflow','paper-enrichment'):
                code='''import importlib.util,json,pathlib,sys
scripts=pathlib.Path(sys.argv[1]); plugin=sys.argv[2]
spec=importlib.util.spec_from_file_location('installed_plugin',scripts/plugin/'__init__.py')
m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
class Context:
 def get_config(self,k,default=None): return sys.argv[3] if k=='python' else str(scripts)
 def register_tool(self,**kw): self.dispatch=kw['handler']
c=Context();m.register(c)
print(c.dispatch(dict(operation='status',attempt_dir=sys.argv[4])))
'''
                result=subprocess.run([sys.executable,'-I','-S','-c',code,str(scripts),plugin,sys.executable,tmp],capture_output=True,text=True)
                self.assertEqual(result.returncode,0,result.stderr)
                value=json.loads(result.stdout)
                self.assertEqual(value['diagnostic'],'operation-job-required',value)

    def test_background_rejects_overlap_before_writing_and_nested_code_outputs(self):
        import operation_jobs as jobs
        from qualified_enrichment.launcher import Deployment,launch
        scripts=Path(jobs.__file__).parent
        d=Deployment(scripts,scripts,scripts,scripts,Path(sys.executable))
        with tempfile.TemporaryDirectory(dir=os.environ['SOURCE_PACKAGE_TEST_ROOT']) as tmp:
            root=Path(tmp); work=root/'work'
            args=dict(operation='article',arguments=dict(command='execute',work_root=str(work)),background=True,attempt_dir=str(work/'attempt'))
            with self.assertRaisesRegex(ValueError,'attempt-must-be-external'): launch(args,d)
            self.assertFalse(work.exists())
            args['attempt_dir']=str(root/'attempt');args['arguments'].update(command='reuse-source',output=str(scripts/'forbidden'),phase='association')
            with self.assertRaisesRegex(ValueError,'write-overlaps-trusted-code'): launch(args,d)
            self.assertFalse((root/'attempt').exists())
            args['arguments']=dict(command='publish',work_root=str(work),remote='test',bucket='test',prefix='test');args['offline']=True
            with self.assertRaisesRegex(ValueError,'offline-publication-forbidden'): launch(args,d)
            self.assertFalse((root/'attempt').exists())

    def test_cancel_during_running_receipt_reaps_child(self):
        from unittest.mock import patch
        from qualified_enrichment import launcher as l
        scripts=Path(l.__file__).parent.parent; children=[]
        d=l.Deployment(scripts,scripts,scripts,scripts,Path(sys.executable))
        original_popen=subprocess.Popen; original_save=l.save
        def spawn(*args,**kwargs):
            child=original_popen([sys.executable,'-c','import time; time.sleep(30)'],**kwargs); children.append(child); return child
        def save(path,value):
            if path.name=='running.json': raise KeyboardInterrupt()
            return original_save(path,value)
        with tempfile.TemporaryDirectory(dir=os.environ['SOURCE_PACKAGE_TEST_ROOT']) as tmp:
            root=Path(tmp)
            args=dict(operation='article',arguments=dict(command='execute',work_root=str(root/'work')),attempt_dir=str(root/'attempt'))
            try:
                with patch.object(l.subprocess,'Popen',side_effect=spawn),patch.object(l,'save',side_effect=save):
                    result=l.launch(args,d)
                self.assertEqual(result['termination'],'cancelled')
                self.assertIsNotNone(children[0].poll())
            finally:
                for child in children:
                    if child.poll() is None: child.kill();child.wait()


class ProgressTests(unittest.TestCase):
    def test_status_reads_worker_configuration_without_dispatch(self):
        import operation_jobs as jobs
        from article_runtime import sha
        with tempfile.TemporaryDirectory(dir=os.environ['SOURCE_PACKAGE_TEST_ROOT']) as tmp:
            root=Path(tmp); package=root/'package'; package.mkdir(); attempt=root/'attempt'; attempt.mkdir()
            args=dict(operation='execute',package_dir=str(package),phase='initial')
            jobs.write(attempt/'job.json',dict(schema='paper-operation-job-v1',created_at=time.time(),
                identity=dict(kind='source',arguments=args)))
            (attempt/'job.sha256').write_text(sha(attempt/'job.json'))
            jobs.write(package/'initial-session.json',dict(vlm_concurrency=12,concurrency_source='environment',started_at='now'))
            result=jobs.status(attempt)
            self.assertEqual(result['execution']['vlm_concurrency'],12)
            self.assertEqual(result['execution']['concurrency_source'],'environment')
            self.assertFalse((attempt/'worker').exists())
            (package/'initial-session.json').write_text('{')
            self.assertEqual(jobs.status(attempt)['execution'],{'status':'updating'})
