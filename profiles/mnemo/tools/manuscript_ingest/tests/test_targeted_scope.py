from test_publication import Publication
from manuscript_ingest import targeted, workflow as w, archive, requests
from unittest.mock import patch
import copy

class Targeted(Publication):
    def test_scope_and_independent_result(self):
        j=self.staged(); manifest=archive.build(j,1,runtime_root=self.runtime); source=archive.verify(manifest)['sources'][0]
        scope=dict(id='operator-specified-table',manifest=str(manifest),manifest_sha256=w.sha(manifest),
            selections=[dict(source_id=source['source_id'],page=1,item='specific result sentence')],objective='Read the reported result sentence',budget=1)
        cfg=w.config(self.runtime); cfg['targeted_scopes']={scope['id']:scope}; cfg['vision']={'model':'fixture','prompt':'Read selected evidence','settings':{}}; w.save(self.runtime/'config.json',cfg)
        with patch.object(requests,'inspect_once',return_value=dict(status='partial',text='Reported effect: 12 percent.',usage={})) as dispatch:
            for changed in ({},dict(scope,authorized=True),dict(scope,selections=[]),dict(scope,objective='all eligible elements')):
                with self.assertRaises(ValueError):targeted.start(changed,invocation_scope=scope,runtime_root=self.runtime)
            altered=copy.deepcopy(scope); altered['selections'][0]['source_id']='other'
            with self.assertRaises(ValueError):targeted.start(altered,invocation_scope=scope,runtime_root=self.runtime)
            with self.assertRaises(ValueError):targeted.run(j,runtime_root=self.runtime)
            self.assertEqual(dispatch.call_count,0)
            t=targeted.start(scope,invocation_scope=scope,runtime_root=self.runtime)
            result=targeted.run(t['job_id'],runtime_root=self.runtime)
            self.assertEqual(result['status'],'partial'); targeted.run(t['job_id'],runtime_root=self.runtime)
            self.assertEqual(dispatch.call_count,1); self.assertEqual(w.status(j,runtime_root=self.runtime)['status'],'ready')
            revised=targeted.revise(t['job_id'],'Qualified as a synthetic example.',runtime_root=self.runtime)
            self.assertEqual(revised['revision'],1); self.assertEqual(dispatch.call_count,1)
