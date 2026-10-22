"""Passwordless household enrollment across gateway and bridge; no public owner bypass."""
import http.server
import json
from pathlib import Path
import tempfile
import threading
import time
import unittest
import urllib.request
import urllib.error
from unittest.mock import patch
from bin import public_gateway_v074 as gateway
from dashboard_bridge import guest_chat
from dashboard_bridge import dashboard_bridge as bridge

class DeviceAccess(unittest.TestCase):
    def setUp(self):
        self.folder=tempfile.TemporaryDirectory();self.addCleanup(self.folder.cleanup)
        for change in (patch.object(guest_chat,'DEVICE_ACCESS',Path(self.folder.name)/'devices.json'),patch.object(bridge,'TOKEN','TEST_OWNER_TOKEN'),patch.object(bridge,'_GUEST_CHAT_MODULE',guest_chat),patch.object(gateway,'owner_token',return_value='TEST_OWNER_TOKEN'),patch.object(bridge,'load_quant_config',return_value={'test':True})):
            change.start();self.addCleanup(change.stop)
        bridge.RATE.clear()
        self.bridge=http.server.ThreadingHTTPServer(('127.0.0.1',0),bridge.Handler)
        threading.Thread(target=self.bridge.serve_forever,daemon=True).start()
        self.addCleanup(self.bridge.server_close);self.addCleanup(self.bridge.shutdown)
        self.base='http://127.0.0.1:'+str(self.bridge.server_port)
        def forward(path,method='GET',body=None,headers=None,timeout=12):
            req=urllib.request.Request(self.base+path,data=body,headers=headers or {},method=method)
            try:
                with urllib.request.build_opener(urllib.request.ProxyHandler({})).open(req,timeout=timeout) as response:
                    return response.status,dict(response.headers),response.read()
            except urllib.error.HTTPError as error:
                return error.code,dict(error.headers),error.read()
        mock=patch.object(gateway,'request_local',side_effect=forward);mock.start();self.addCleanup(mock.stop)
        self.gateway=http.server.ThreadingHTTPServer(('127.0.0.1',0),gateway.Handler)
        threading.Thread(target=self.gateway.serve_forever,daemon=True).start()
        self.addCleanup(self.gateway.server_close);self.addCleanup(self.gateway.shutdown)
        self.url='http://127.0.0.1:'+str(self.gateway.server_port)
    def call(self,path,body=None,headers=None):
        req=urllib.request.Request(self.url+path,data=json.dumps(body).encode() if body is not None else None,headers={'Content-Type':'application/json',**(headers or {})})
        try:
            with urllib.request.build_opener(urllib.request.ProxyHandler({})).open(req,timeout=4) as response:return response.status,json.load(response)
        except urllib.error.HTTPError as error:
            with error:return error.code,json.load(error)
    def test_request_approval_same_full_owner_controls(self):
        code,request=self.call('/dashboard/device-access/request',{'name':"Wife's phone"});self.assertEqual(code,200)
        device={'X-Myles-Device':request['request_token']};owner={'X-Myles-Token':'TEST_OWNER_TOKEN'}
        self.assertEqual(self.call('/dashboard/device-access/status',headers=device)[1]['status'],'pending')
        self.assertNotIn('token',self.call('/dashboard/device-access/status',headers=device)[1])
        self.assertEqual(self.call('/dashboard/quant/config',headers=device)[0],401)
        self.assertEqual(self.call('/dashboard/device-access/pending')[0],401)
        _,pending=self.call('/dashboard/device-access/pending',headers=owner)
        self.assertNotIn('secret_hash',str(pending));self.assertNotIn(request['request_token'],str(pending))
        request_id=pending['requests'][0]['id']
        self.assertEqual(self.call('/dashboard/device-access/approve',{'request_id':request_id},device)[0],401)
        self.assertEqual(self.call('/dashboard/device-access/approve',{'request_id':request_id},owner)[0],200)
        code,status=self.call('/dashboard/device-access/status',headers=device)
        self.assertEqual(code,200);self.assertEqual(status['role'],'household_owner');self.assertEqual(status['token'],'TEST_OWNER_TOKEN')
        self.assertEqual(self.call('/dashboard/quant/config',headers={'X-Myles-Token':status['token']})[1]['config'],{'test':True})
        self.assertNotIn('TEST_OWNER_TOKEN',guest_chat.DEVICE_ACCESS.read_text())
    def test_expiry_denial_wrong_secret_and_token_rotation(self):
        request=guest_chat.request_device_access('Phone');secret=request['request_token'];row=guest_chat.pending_devices()['requests'][0]
        self.assertIsNone(guest_chat.device_access_status('x'*48,'TEST_OWNER_TOKEN'))
        guest_chat.decide_device(row['id'],False,'TEST_OWNER_TOKEN')
        self.assertEqual(guest_chat.device_access_status(secret,'TEST_OWNER_TOKEN')['status'],'denied')
        request2=guest_chat.request_device_access('Second');row=guest_chat.pending_devices()['requests'][0]
        guest_chat.decide_device(row['id'],True,'TEST_OWNER_TOKEN')
        self.assertIsNone(guest_chat.device_access_status(request2['request_token'],'ROTATED_TOKEN'))
        with patch.object(guest_chat.time,'time',return_value=time.time()+601):
            self.assertIsNone(guest_chat.device_access_status(secret,'TEST_OWNER_TOKEN'))
    def test_exact_routes_and_origin_only(self):
        self.assertEqual(self.call('/dashboard/device-access/request/anything',{})[0],405)
        self.assertEqual(self.call('/dashboard/device-access/request',{'name':'Phone'}, {'Origin':'https://untrusted.example'})[0],403)
        self.assertEqual(self.call('/dashboard/device-access/request',{'name':'x'*61})[0],400)

if __name__=='__main__':unittest.main()
