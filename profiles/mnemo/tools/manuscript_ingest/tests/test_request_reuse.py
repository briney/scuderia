import multiprocessing
from pathlib import Path
import sys
import tempfile
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from manuscript_ingest import requests

def compete(ledger,queue):
    queue.put(requests.reserve('source-op',ledger=ledger,job_id='job',authorization={'max_requests':2})['dispatch'])

class Requests(unittest.TestCase):
    def test_atomic_reservation_and_recovery(self):
        with tempfile.TemporaryDirectory() as raw:
            ledger=Path(raw).resolve()/'requests.sqlite'; q=multiprocessing.Queue()
            ps=[multiprocessing.Process(target=compete,args=(ledger,q)) for _ in range(2)]
            for p in ps:p.start()
            for p in ps:p.join(); self.assertEqual(p.exitcode,0)
            self.assertEqual(sorted(q.get() for _ in ps),[False,True])
            self.assertFalse(requests.reserve('source-op',ledger=ledger,job_id='copied-directory',authorization={'max_requests':2})['dispatch'])
            requests.finish('source-op',ledger=ledger,outcome={'status':'success','text':'evidence'})
            reused=requests.reserve('source-op',ledger=ledger,job_id='new-job',authorization={'max_requests':2})
            self.assertEqual(reused['outcome']['text'],'evidence'); self.assertFalse(reused['dispatch'])
    def test_no_automatic_retry_and_budget(self):
        with tempfile.TemporaryDirectory() as raw:
            p=Path(raw).resolve()/'requests.sqlite'; auth={'max_requests':1}
            requests.reserve('x',ledger=p,job_id='j',authorization=auth)
            requests.finish('x',ledger=p,outcome={'status':'failed'})
            self.assertFalse(requests.reserve('x',ledger=p,job_id='other',authorization=auth)['dispatch'])
            self.assertFalse(requests.reserve('y',ledger=p,job_id='j',authorization=auth)['dispatch'])
            retry=requests.reserve('x',ledger=p,job_id='j',authorization={'max_requests':2,'retry_id':'operator-one','retry_key':'x'})
            self.assertTrue(retry['dispatch']); self.assertEqual(retry['predecessor'],'x')
            self.assertFalse(requests.reserve('x',ledger=p,job_id='j',authorization={'max_requests':2,'retry_id':'operator-one','retry_key':'x'})['dispatch'])
