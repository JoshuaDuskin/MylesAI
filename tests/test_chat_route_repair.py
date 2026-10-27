import io, tempfile, unittest, http.server, threading, json, urllib.request
from unittest.mock import patch
from dashboard_bridge import dashboard_bridge as bridge
from dashboard_bridge import guest_chat
from dashboard_bridge.chat_delivery import DeliveryQueue
from bin import public_gateway_v074 as gateway

class ChatRouteRepair(unittest.TestCase):
    def test_authenticated_public_alias_reaches_owner_not_guest(self):
        with tempfile.TemporaryDirectory() as folder:
            q=DeliveryQueue(folder)
            with patch.object(bridge,'TOKEN','OWNER_TEST'),patch.object(bridge,'chat_delivery',return_value=q),patch.object(bridge,'send_owner_delivery',return_value=(200,{'reply':'Owner result','message_id':23})),patch.object(bridge,'core_json',return_value=(200,{'messages':[]})),patch.object(bridge,'guest_request_rate',side_effect=AssertionError('Owner reached guest quota')):
                server=http.server.ThreadingHTTPServer(('127.0.0.1',0),bridge.Handler)
                threading.Thread(target=server.serve_forever,daemon=True).start()
                try:
                    base=f'http://127.0.0.1:{server.server_port}/dashboard/public-chat/messages'
                    opener=urllib.request.build_opener(urllib.request.ProxyHandler({}))
                    body=json.dumps({'message':'Hello','client_request_id':'owner_alias_request_123'}).encode()
                    with opener.open(urllib.request.Request(base,data=body,headers={'Authorization':'Bearer OWNER_TEST','Content-Type':'application/json'})) as response:
                        self.assertEqual(response.status,202)
                    with opener.open(urllib.request.Request(base,headers={'Authorization':'Bearer OWNER_TEST'})) as response:
                        self.assertEqual(json.load(response)['role'],'owner')
                    self.assertEqual(q.snapshot('public'),[])
                    self.assertEqual(q.snapshot('owner')[0]['message'],'Hello')
                finally:server.shutdown();server.server_close();q.executor.shutdown(wait=True)

    def test_history_polling_cannot_exhaust_the_send_quota(self):
        handler=type('Request',(),{'headers':{}})()
        with bridge.RATE_LOCK:bridge.RATE.clear()
        for _ in range(100):self.assertTrue(bridge.guest_request_rate(handler,False))
        for _ in range(20):self.assertTrue(bridge.guest_request_rate(handler,True))
        self.assertFalse(bridge.guest_request_rate(handler,True))

    def test_duplicate_request_does_not_spend_quota_or_reexecute(self):
        with tempfile.TemporaryDirectory() as folder:
            q=DeliveryQueue(folder);calls=[]
            q.submit('public','replay_request_12345','hello',lambda text:(calls.append(text) or 200,{'reply':'Hello'}))
            q.executor.shutdown(wait=True)
            code,_=q.submit('public','replay_request_12345','hello',lambda _:self.fail('Replay'),admit=lambda:self.fail('Quota'))
            self.assertEqual(code,202);self.assertEqual(calls,['hello'])

    def test_gateway_retains_owner_credentials_on_public_route(self):
        h=object.__new__(gateway.Handler);h.path='/dashboard/public-chat/messages';h.command='POST'
        h.headers={'Authorization':'Bearer OWNER_TEST'};h.rfile=io.BytesIO(b'')
        with patch.object(gateway,'owner_token',return_value='OWNER_TEST'),patch.object(h,'proxy',return_value='owner') as route:
            self.assertEqual(h.proxy_public_chat(),'owner');self.assertEqual(h.path,'/dashboard/messages');route.assert_called_once()

    def test_ambiguous_timeout_never_replays_through_legacy_routes(self):
        with patch.object(bridge,'core_json',return_value=(599,{'error':'Timed out'})) as call:
            self.assertEqual(bridge.send_to_myles('Close Notepad')[0],599)
            self.assertEqual(call.call_count,1)

    def test_visitor_desktop_refusal_names_session_scope_not_missing_tools(self):
        with patch('myles_game_guard.game_is_active',return_value=False):
            code,result=guest_chat.public_send('Close chat gpt')
        self.assertEqual(code,403);self.assertIn('installed',result['reply']);self.assertIn('not owner-authorized',result['reply'])
