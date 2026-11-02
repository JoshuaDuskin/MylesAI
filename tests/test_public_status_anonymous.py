"""Only the scrubbed status/health routes are readable without a token."""
import http.server
import json
import threading
import urllib.error
import urllib.request
import unittest
from unittest.mock import patch

from bin import public_gateway_v074 as gateway


class AnonymousStatusTests(unittest.TestCase):
    def test_status_and_health_are_scrubbed_public_routes(self):
        with patch.object(gateway, "compact_status", return_value=(200, {"ok": True, "myles": {"online": True}})), \
             patch.object(gateway, "request_local", return_value=(200, {}, b"{}")):
            server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), gateway.Handler)
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            base = f"http://127.0.0.1:{server.server_port}"
            opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
            try:
                for path in ("/dashboard/status", "/api/public-status", "/dashboard/health"):
                    with self.subTest(path=path):
                        with opener.open(urllib.request.Request(base + path), timeout=4) as response:
                            self.assertEqual(response.status, 200)
                request = urllib.request.Request(base + "/dashboard/quant/config")
                with self.assertRaises(urllib.error.HTTPError) as error:
                    opener.open(request, timeout=4)
                self.assertEqual(error.exception.code, 401)
            finally:
                server.shutdown(); server.server_close(); thread.join(timeout=3)


if __name__ == "__main__":
    unittest.main()
