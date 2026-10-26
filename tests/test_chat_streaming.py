import json,unittest
from types import SimpleNamespace
from unittest.mock import patch
from myles_model_runtime import model_chat_stream,ModelRuntimeError
class Response:
 def __init__(self,rows):self.rows=rows
 def __enter__(self):return self
 def __exit__(self,*args):pass
 def __iter__(self):return iter(json.dumps(r).encode() for r in self.rows)
class StreamingTests(unittest.TestCase):
 def test_real_chunks_are_reported_before_a_verified_done_marker(self):
  rows=[{'message':{'content':'Hello','thinking':'private'}},{'message':{'content':' world'}},{'done':True,'done_reason':'stop'}];parts=[]
  with patch('myles_game_guard.game_is_active',return_value=False),patch('myles_model_runtime.ensure_model_runtime',return_value=SimpleNamespace(available=True,model='test')),patch('myles_model_runtime.urllib.request.urlopen',return_value=Response(rows)):
   result=model_chat_stream({},[],parts.append)
  self.assertEqual(parts,['Hello','Hello world']);self.assertEqual(result['message']['content'],'Hello world');self.assertNotIn('thinking',result['message'])
 def test_incomplete_stream_is_not_completed(self):
  with patch('myles_game_guard.game_is_active',return_value=False),patch('myles_model_runtime.ensure_model_runtime',return_value=SimpleNamespace(available=True,model='test')),patch('myles_model_runtime.urllib.request.urlopen',return_value=Response([{'message':{'content':'Partial'}}])):
   with self.assertRaises(ModelRuntimeError):model_chat_stream({},[],lambda _:None)
 def test_game_start_interrupts_stream(self):
  with patch('myles_game_guard.game_is_active',side_effect=[False,True]),patch('myles_model_runtime.ensure_model_runtime',return_value=SimpleNamespace(available=True,model='test')),patch('myles_model_runtime.urllib.request.urlopen',return_value=Response([{'message':{'content':'Partial'}}])):
   with self.assertRaisesRegex(ModelRuntimeError,'game_performance'):model_chat_stream({},[],lambda _:None)
