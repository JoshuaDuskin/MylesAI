import tempfile,threading,unittest,time
from pathlib import Path
from dashboard_bridge.chat_delivery import DeliveryQueue

class ChatDeliveryTests(unittest.TestCase):
 def test_ack_is_independent_of_execution_and_retry_is_idempotent(self):
  with tempfile.TemporaryDirectory() as folder:
   q=DeliveryQueue(folder);entered=threading.Event();release=threading.Event();calls=[]
   def slow(text):
    calls.append(text);entered.set();release.wait(3);return 200,{"ok":True,"reply":"Verified result"}
   started=time.perf_counter();code,data=q.submit('public','chat_request_123456','hello',slow)
   self.assertEqual(code,202);self.assertLess(time.perf_counter()-started,.2)
   self.assertTrue(entered.wait(1));self.assertEqual(q.submit('public','chat_request_123456','hello',slow)[0],202)
   self.assertEqual(q.submit('public','chat_request_123456','different',slow)[0],409)
   self.assertEqual(q.snapshot('owner'),[]);self.assertEqual(q.snapshot('public')[0]['status'],'Running')
   release.set();q.executor.shutdown(wait=True);self.assertEqual(calls,['hello']);self.assertEqual(q.snapshot('public')[0]['status'],'Completed')
 def test_failures_and_restart_never_claim_completion(self):
  with tempfile.TemporaryDirectory() as folder:
   q=DeliveryQueue(folder)
   q.submit('owner','chat_request_123456','run',lambda _: (503,{'error':'Model unavailable'}));q.executor.shutdown(wait=True)
   self.assertEqual(q.snapshot('owner')[0]['status'],'Failed')
   q.records['owner'][0]['status']='Running';q.save('owner')
   recovered=DeliveryQueue(folder);self.assertEqual(recovered.snapshot('owner')[0]['status'],'Failed');recovered.executor.shutdown()
 def test_job_completion_uses_real_job_state(self):
  with tempfile.TemporaryDirectory() as folder:
   q=DeliveryQueue(folder);q.submit('owner','chat_request_123456','work',lambda _: (200,{'reply':'Queued','job_id':'actual-job'}));q.executor.shutdown(wait=True)
   self.assertEqual(q.snapshot('owner',lambda _: {'state':'running','phase':'tool'})[0]['status'],'Running')
   self.assertEqual(q.snapshot('owner',lambda _: {'state':'failed','error':'Actual tool failure'})[0]['status'],'Failed')
 def test_unverified_action_is_failed(self):
  with tempfile.TemporaryDirectory() as folder:
   q=DeliveryQueue(folder);q.submit('public','chat_request_123456','open',lambda _: (200,{'ok':True,'reply':"I couldn't verify that it opened."}));q.executor.shutdown(wait=True)
   self.assertEqual(q.snapshot('public')[0]['status'],'Failed')

 def test_known_jobs_resume_tracking_after_bridge_restart_without_reexecution(self):
  with tempfile.TemporaryDirectory() as folder:
   q=DeliveryQueue(folder);q.submit('owner','chat_request_123456','work',lambda _: (200,{'reply':'Queued','job_id':'preserved-job'}));q.executor.shutdown(wait=True)
   recovered=DeliveryQueue(folder);self.assertEqual(recovered.snapshot('owner',lambda _: {'state':'running'})[0]['status'],'Running')
   self.assertEqual(recovered.snapshot('owner',lambda _: {'state':'done'})[0]['status'],'Completed');recovered.executor.shutdown()
