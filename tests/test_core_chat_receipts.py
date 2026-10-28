import tempfile, unittest
from pathlib import Path
from unittest.mock import patch
from myles_chat_receipts import OwnerReceipts
from dashboard_bridge.chat_delivery import DeliveryQueue
import myles_core as core

class CoreChatReceipts(unittest.TestCase):
    def test_core_idempotency_survives_restart_and_rejects_changed_message(self):
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'receipts.json';store=OwnerReceipts(path);identifier='core_request_123456'
            self.assertIsNone(store.begin(identifier,'close QA','dashboard'))
            restarted=OwnerReceipts(path)
            self.assertEqual(restarted.begin(identifier,'close QA','dashboard')[0],202)
            self.assertEqual(restarted.begin(identifier,'other','dashboard')[0],409)
            restarted.finish(identifier,{'reply':'Closed QA','message_id':12})
            self.assertEqual(OwnerReceipts(path).begin(identifier,'close QA','dashboard'),(200,{'reply':'Closed QA','message_id':12}))

    def test_late_result_recovers_failed_delivery_without_reexecution(self):
        with tempfile.TemporaryDirectory() as folder:
            q=DeliveryQueue(folder)
            q.submit('owner','core_request_123456','close QA',lambda _: (599,{'error':'HTTP timeout'}));q.executor.shutdown(wait=True)
            self.assertEqual(q.snapshot('owner')[0]['status'],'Failed')
            receipt={'message':'close QA','finished_at':42,'result':{'ok':True,'reply':'Closed QA','message_id':12,'user_message_id':11}}
            row=q.snapshot('owner',result_reader=lambda _:receipt)[0]
            self.assertEqual(row['status'],'Completed');self.assertEqual(row['reply_message_id'],12)
            self.assertNotIn('error',row)
            self.assertEqual(q.submit('owner','core_request_123456','close QA',lambda _:self.fail('Replay'))[0],202)

    def test_presence_check_does_not_start_model_or_worker(self):
        with patch.object(core,'add_message',return_value=1),patch.object(core,'_conversation_agent_turn') as model,patch.object(core,'_start_task') as worker:
            result=core.handle_owner_message('Hello?','dashboard')
            self.assertIn("I'm here",result['reply']);model.assert_not_called();worker.assert_not_called()
