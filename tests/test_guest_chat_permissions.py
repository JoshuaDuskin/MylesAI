"""Guest-only family chat: no owner permissions even on the public gateway."""
from __future__ import annotations
import http.server
import json
import tempfile
import threading
import unittest
import urllib.error
import urllib.request
from pathlib import Path
from unittest.mock import patch

from dashboard_bridge import guest_chat
from dashboard_bridge import dashboard_bridge as bridge
from bin import public_gateway_v074 as gateway


def request(base,path,*,method="GET",payload=None,headers=None):
    data=json.dumps(payload).encode("utf-8") if payload is not None else None
    r=urllib.request.Request(base+path,data=data,method=method,
        headers={"Content-Type":"application/json",**(headers or {})})
    opener=urllib.request.build_opener(urllib.request.ProxyHandler({}))
    try:
        with opener.open(r,timeout=4) as ans:
            return ans.status,json.loads(ans.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        return exc.code,json.loads(exc.read().decode("utf-8"))


class GuestRoleTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        d=Path(self.temp.name)
        self.patchers=[
            patch.object(guest_chat,"AUTH",d/"guest_auth.json"),
            patch.object(guest_chat,"HISTORY",d/"guest_history.json"),
        ]
        for p in self.patchers:p.start()
    def tearDown(self):
        for p in reversed(self.patchers):p.stop()
        self.temp.cleanup()

    def test_single_use_code_hashing_revocation_and_separate_history(self):
        invite=guest_chat.make_invite()
        code=invite["code"]
        self.assertEqual(len(code),8)
        self.assertNotIn(code,guest_chat.AUTH.read_text())
        self.assertIsNone(guest_chat.exchange("WRONG123"))
        paired=guest_chat.exchange(code)
        self.assertEqual(paired["role"],"guest_chat_only")
        self.assertNotIn(paired["token"],guest_chat.AUTH.read_text())
        self.assertIsNone(guest_chat.exchange(code))
        self.assertTrue(guest_chat.is_guest(paired["token"]))
        self.assertFalse(guest_chat.is_guest("owner-something-longer-than-32-characters"))
        self.assertEqual(guest_chat.messages()["messages"],[])
        guest_chat.revoke()
        self.assertFalse(guest_chat.is_guest(paired["token"]))

    def test_guest_model_is_text_only_no_private_history_or_tools(self):
        fake={"message":{"content":"Hello! I can help with general questions."},
              "done_reason":"stop"}
        with patch("myles_game_guard.game_is_active",return_value=False), \
             patch("myles_common.load_config",return_value={}), \
             patch("myles_model_runtime.model_chat",return_value=fake) as model:
            status,result=guest_chat.send("Hi Myles")
        self.assertEqual(status,200)
        self.assertEqual(result["role"],"guest_chat_only")
        self.assertEqual([m["role"] for m in result["messages"]],["user","assistant"])
        args=model.call_args
        self.assertIsNone(args.kwargs["tools"])
        context=args.args[1]
        self.assertEqual(context[-1],{"role":"user","content":"Hi Myles"})
        self.assertNotIn("owner task",json.dumps(context[-2:]))
        self.assertIn("NO permission",context[0]["content"])
        self.assertNotIn("ownerToken",json.dumps(result))

    def test_guest_message_cannot_run_during_game(self):
        with patch("myles_game_guard.game_is_active",return_value=True), \
             patch("myles_model_runtime.model_chat") as call:
            status,payload=guest_chat.send("Open Fortnite")
        self.assertEqual(status,503)
        call.assert_not_called()

    def test_bridge_routes_enforce_owner_vs_guest_separately(self):
        old_token=bridge.TOKEN
        bridge.TOKEN="test-owner-token-not-the-guest"
        server=http.server.ThreadingHTTPServer(("127.0.0.1",0),bridge.Handler)
        thread=threading.Thread(target=server.serve_forever,daemon=True)
        thread.start()
        url="http://127.0.0.1:"+str(server.server_port)
        try:
            code,_=request(url,"/dashboard/guest/invite",method="POST",payload={})
            self.assertEqual(code,401)
            code,data=request(url,"/dashboard/guest/invite",method="POST",payload={},
                   headers={"X-Myles-Token":bridge.TOKEN})
            self.assertEqual(code,200)
            token=request(url,"/dashboard/guest/pair",method="POST",
                    payload={"code":data["code"]})[1]["token"]
            self.assertNotEqual(token,bridge.TOKEN)
            guest={"X-Myles-Guest":token}
            code,data=request(url,"/dashboard/guest/messages",headers=guest)
            self.assertEqual(code,200)
            self.assertEqual(data["messages"],[])
            # Every privileged owner endpoint must refuse guest credentials.
            for path,method,payload in (
                ("/dashboard/messages","GET",None),
                ("/dashboard/status","GET",None),
                ("/dashboard/control/continuous","POST",{"enabled":True}),
                ("/dashboard/quant/action","POST",{"action":"reset_paper"}),
                ("/dashboard/quant/live/order","POST",{"action":"open"}),
                ("/dashboard/quant/config","POST",{"paper":{"auto_trading_enabled":True}}),
            ):
                with self.subTest(path=path):
                    code,_=request(url,path,method=method,payload=payload,headers=guest)
                    self.assertEqual(code,401)
            code,_=request(url,"/dashboard/guest/revoke",method="POST",payload={},headers=guest)
            self.assertEqual(code,401)
            code,_=request(url,"/dashboard/guest/revoke",method="POST",payload={},
                           headers={"X-Myles-Token":bridge.TOKEN})
            self.assertEqual(code,200)
            code,_=request(url,"/dashboard/guest/messages",headers=guest)
            self.assertEqual(code,401)
        finally:
            server.shutdown();server.server_close();thread.join(timeout=3)
            bridge.TOKEN=old_token

    def test_public_gateway_rejects_guest_on_owner_routes(self):
        with patch.object(gateway,"owner_token",return_value="OWNER_SECRET"), \
             patch.object(gateway,"request_local") as forward:
            server=http.server.ThreadingHTTPServer(("127.0.0.1",0),gateway.Handler)
            thread=threading.Thread(target=server.serve_forever,daemon=True)
            thread.start()
            url="http://127.0.0.1:"+str(server.server_port)
            try:
                headers={"X-Myles-Guest":"a"*48}
                for path in ("/dashboard/quant/action","/dashboard/quant/live/order",
                             "/dashboard/messages","/dashboard/guest/invite"):
                    with self.subTest(path=path):
                        code,_=request(url,path,method="POST",payload={},headers=headers)
                        self.assertEqual(code,401)
                forward.assert_not_called()
            finally:
                server.shutdown();server.server_close();thread.join(timeout=3)

    def test_household_links_use_one_dashboard(self):
        html=(Path(__file__).resolve().parents[1]/"index.html").read_text(encoding="utf-8")
        self.assertNotIn("initGuestChat", html)
        self.assertNotIn('id="guestShell"', html)
        self.assertNotIn("guest.ownerToken", html)
        self.assertIn("['shared','guest','owner']", html)
        self.assertIn("history.replaceState", html)
        self.assertIn("function dashboardUrl(){return location.origin+(location.pathname||'/');}", html)
        self.assertIn("if(state.bridge.healthy&&state.bridge.token&&state.publicMode)", html)


if __name__=="__main__":
    unittest.main()
