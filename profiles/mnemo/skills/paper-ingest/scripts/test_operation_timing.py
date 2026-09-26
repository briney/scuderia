"""Operational timing is diagnostic; it never authorizes replay or publication."""
import os
from pathlib import Path
import tempfile
import unittest
import portable_articles as pa

class TimingTests(unittest.TestCase):
    def test_failed_replacement_and_reused_calls_use_interval_union(self):
        import operation_timing as timing
        with tempfile.TemporaryDirectory(dir=os.environ['SOURCE_PACKAGE_TEST_ROOT']) as tmp:
            root=Path(tmp)
            def attempt(name, rows):
                work=root/name; work.mkdir()
                pa.save(work/'initial-plan.json',dict(requests=[dict(directory=str(i)) for i in range(len(rows))]))
                pa.save(work/'initial-session.json',dict(started_at='2026-01-01T00:00:00Z',vlm_concurrency=12,concurrency_source='environment'))
                for i,(identity,start,end,complete) in enumerate(rows):
                    d=work/str(i); d.mkdir()
                    pa.save(d/'reservation.json',dict(identity=identity))
                    pa.save(d/'call.json',dict(started_at=f'2026-01-01T00:00:{start:02}Z',ended_at=f'2026-01-01T00:00:{end:02}Z',
                        complete=complete,status='completed' if complete else 'http-failure',usage=dict(prompt_tokens=2,completion_tokens=3,total_tokens=5)))
                return work
            old=attempt('failed',[(1,0,10,False)])
            new=attempt('replacement',[(2,5,15,True),(3,12,20,True)])
            reused=attempt('reused',[(2,5,15,True)])
            result=timing.summarize(source_attempts=[old,new,reused])
            self.assertEqual(result['counts'],dict(total=3,successful=2,failed=1,uncertain=0,reused=1))
            self.assertEqual(result['request_wall_seconds'],20)
            self.assertEqual(result['request_elapsed_sum_seconds'],28)
            self.assertEqual(result['usage']['total_tokens'],15)
            self.assertEqual(result['attempts'][0]['phases'][0]['concurrency_source'],'environment')
            self.assertEqual(result['requests'][0]['response_received_at'],None)
            self.assertEqual(timing.summarize()['request_wall_seconds'],None)
