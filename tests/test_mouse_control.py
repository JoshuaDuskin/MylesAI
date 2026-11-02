"""Owner-authenticated mouse session and bounded input routing."""
import http.server
import json
import threading
import urllib.error
import urllib.request
import unittest
from unittest.mock import patch

from dashboard_bridge import dashboard_bridge as bridge


def request(base, path, *, method="GET", payload=None, headers=None):
    data = json.dumps(payload).encode("utf-8") if payload is not None else None
    req = urllib.request.Request(base + path, data=data, method=method,
                                 headers={"Content-Type": "application/json", **(headers or {})})
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    try:
        with opener.open(req, timeout=4) as ans:
            return ans.status, json.loads(ans.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        return exc.code, json.loads(exc.read().decode("utf-8"))


class MouseControlTests(unittest.TestCase):
    def setUp(self):
        self.old_token = bridge.TOKEN
        bridge.TOKEN = "test-owner-token"
        bridge.MOUSE_SESSIONS.clear()
        self.server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), bridge.Handler)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.base = f"http://127.0.0.1:{self.server.server_port}"

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=3)
        bridge.MOUSE_SESSIONS.clear()
        bridge.TOKEN = self.old_token

    def test_requires_owner_and_releases_session(self):
        code, _ = request(self.base, "/dashboard/mouse/session", method="POST", payload={})
        self.assertEqual(code, 401)
        auth = {"X-Myles-Token": bridge.TOKEN}
        with patch("myles_tools.desktop_mouse_input", return_value='{"ok":true,"events":0}') as mouse:
            code, data = request(self.base, "/dashboard/mouse/session", method="POST", payload={}, headers=auth)
            self.assertEqual(code, 200)
            sid = data["session_id"]
            code, state = request(self.base, "/dashboard/mouse/state", headers=auth)
            self.assertEqual((code, state["active_sessions"]), (200, 1))
            code, result = request(self.base, "/dashboard/mouse/input", method="POST", headers=auth,
                                   payload={"session_id": sid, "events":[{"type":"move", "dx": 3, "dy": -2}, {"type":"button", "button":"left", "state":"down"}]})
            self.assertEqual(code, 200)
            self.assertEqual(result["result"]["events"], 0)
            self.assertEqual(len(mouse.call_args.args[1]), 2)
            mouse.assert_called_once()
            code, result = request(self.base, "/dashboard/mouse/disconnect", method="POST", headers=auth,
                                   payload={"session_id": sid})
            self.assertEqual((code, result["disconnected"]), (200, True))
            self.assertEqual(mouse.call_args.args[1][-1], {"type":"button", "button":"left", "state":"up"})

    def test_batches_are_bounded_and_invalid_numbers_are_rejected(self):
        auth = {"X-Myles-Token": bridge.TOKEN}
        with patch("myles_tools.desktop_mouse_input", return_value='{"ok":true,"events":0}'):
            _, data = request(self.base, "/dashboard/mouse/session", method="POST", payload={}, headers=auth)
            sid = data["session_id"]
            code, _ = request(self.base, "/dashboard/mouse/input", method="POST", headers=auth,
                              payload={"session_id": sid, "events":[{"type":"move", "dx": None, "dy": 0}]})
            self.assertEqual(code, 400)
            code, _ = request(self.base, "/dashboard/mouse/input", method="POST", headers=auth,
                              payload={"session_id": sid, "events":[{"type":"move", "dx": 0, "dy": 0}] * 101})
            self.assertEqual(code, 400)


if __name__ == "__main__":
    unittest.main()
