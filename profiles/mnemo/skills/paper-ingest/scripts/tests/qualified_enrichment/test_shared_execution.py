"""Both callers use one locked, reservation-first executor; transport doubles only."""
import fcntl
import json
import os
import unittest
from unittest.mock import patch
import article_enrichment as ae
import portable_articles as pa
import reenrich as rr
import test_reenrich as fixtures
from test_reenrich import count_and_approve, inference_double


class SharedExecution(unittest.TestCase):
    setUp = fixtures.ReenrichTests.setUp
    plan = fixtures.ReenrichTests.plan

    def prepared(self):
        self.plan(selected=False)
        rr.advance(self.work, 'prepare')
        return count_and_approve(self.work, self.base)

    def test_local_failure_continues(self):
        approval = self.prepared(); good = inference_double(self.work); sent = []
        def transport(payload, row):
            sent.append(row['id'])
            response=good(payload,row)
            if len(sent)==1:
                envelope=json.loads(response['raw']); envelope['choices'][0]['message']['content']='{}'
                response['raw']=json.dumps(envelope).encode()
            return response
        state = rr.advance(self.work, 'approved-execute', approval=approval, fixture_transport=transport)
        self.assertEqual(len(sent), 2)
        self.assertEqual(state['accounting']['counts']['failed'], 1)
        self.assertEqual(state['accounting']['counts']['completed'], 1)
        again=rr.advance(self.work,'approved-execute',approval=approval,
                         fixture_transport=lambda *a:self.fail('consumed request reposted'))
        self.assertEqual(state,again)

    def test_direct_execute_is_locked(self):
        approval=self.prepared(); _,_,manifest,_,_,binding,_=rr.context(self.work)
        with (self.work/'enrichment/operation.lock').open('a+b') as lock:
            fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
            with self.assertRaises(BlockingIOError):
                ae.execute(self.work,binding,manifest,approval,
                           fixture_transport=lambda *a:self.fail('post while locked'))
        self.assertFalse((self.work/'enrichment/execution-start.json').exists())

    def test_pre_post_mutation_sends_nothing(self):
        calls=[]
        class Opener:
            def open(self,*a,**k): calls.append('POST'); raise AssertionError('must not post')
        with patch.dict(os.environ,{'SYNTHETIC_KEY':'not-a-secret'}), \
             patch.object(ae.urllib.request,'build_opener',return_value=Opener()):
            with self.assertRaisesRegex(ValueError,'changed'):
                ae._post(b'{}',dict(credential_env='SYNTHETIC_KEY',endpoint='https://example.invalid/',timeout_seconds=1200),
                         lambda: (_ for _ in ()).throw(ValueError('changed')))
        self.assertFalse(calls)

    def test_reserved_interruption_only_resumes_never_sent(self):
        approval=self.prepared(); sent=[]
        def crash(payload,row): sent.append(row['id']); raise KeyboardInterrupt()
        with self.assertRaises(KeyboardInterrupt):
            rr.advance(self.work,'approved-execute',approval=approval,fixture_transport=crash)
        good=inference_double(self.work)
        def resume(payload,row): sent.append(row['id']); return good(payload,row)
        state=rr.advance(self.work,'approved-execute',approval=approval,fixture_transport=resume)
        self.assertEqual(len(sent),len(set(sent)))
        self.assertEqual(state['accounting']['counts']['uncertain'],1)
        self.assertEqual(state['accounting']['counts']['completed'],1)

    def test_fatal_route_count_and_auth_stop_siblings(self):
        approval=self.prepared(); sent=[]
        def denied(payload,row): sent.append(row['id']); return dict(http_status=401,raw=b'{}')
        with self.assertRaises(ValueError):
            rr.advance(self.work,'approved-execute',approval=approval,fixture_transport=denied)
        self.assertEqual(len(sent),1)
        with self.assertRaisesRegex(ValueError,'integrity-hold'):
            rr.advance(self.work,'approved-execute',approval=approval,fixture_transport=lambda *a:self.fail('fatal resumed'))
