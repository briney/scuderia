import importlib.util
from pathlib import Path
import subprocess
import sys
import unittest
from test_jobs import Jobs
from manuscript_ingest import cli

SCRIPTS=Path(__file__).resolve().parents[3]/'skills/paper-ingest/scripts'
class Discovery(Jobs):
    def test_modern_operations_and_refused_escalation(self):
        self.assertEqual(set(cli.OPERATIONS),{'start','sources','read','stage','publish','status'})
        for args in ({'operation':'execute'},{'operation':'article','arguments':{'command':'route'}},{'operation':'start','page':str(self.page),'authorized':True}):
            with self.assertRaises(ValueError):cli.dispatch(args,runtime_root=self.runtime)
        from manuscript_ingest.hermes import SCHEMA
        self.assertNotIn('arguments',SCHEMA['parameters']['properties'])
        self.assertNotIn('targeted',str(SCHEMA))
    def test_retired_direct_entries(self):
        for name in ('entry.py','operate.py','initial_ingest.py','reenrich.py','pdf_source_package/cli.py','pdf_source_package/launcher.py','pdf_enrichment/cli.py','qualified_enrichment/launcher.py'):
            process=subprocess.run([sys.executable,'-B',str(SCRIPTS/name),'execute'],capture_output=True,text=True)
            self.assertEqual(process.returncode,2,(name,process.stderr)); self.assertIn('retired-workflow',process.stdout)
        for name in ('paper-workflow','paper-enrichment','paper-vision'):
            path=SCRIPTS/name/'__init__.py'
            if path.exists():
                spec=importlib.util.spec_from_file_location('retired_plugin',path); module=importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
                class Spy:
                    def register_tool(self,**kwargs):raise AssertionError('obsolete registration')
                module.register(Spy())
    def test_no_active_exhaustive_instructions(self):
        skill=SCRIPTS.parent
        for name in ('qualified-enrichment.md','qualified-enrichment-schema.md','source-package-integration.md','portable-articles.md'):
            self.assertFalse((skill/'references'/name).exists())
        self.assertFalse((SCRIPTS/'pdf_source_package/execution.py').exists())
        self.assertFalse((SCRIPTS/'pdf_enrichment/live.py').exists())
