"""The compact phone payload must support the Research tab, not invent paused/zero state."""
import json
import unittest
from unittest.mock import patch
from bin import public_gateway_v074 as gateway

class QuantDashboardStatus(unittest.TestCase):
    def test_research_and_main_account_survive_compact_status(self):
        trading = {"equity": 10060, "total_pnl": 60,
                   "research_lab": {"enabled": True, "tested_candidates": 9},
                   "research_paper": {"pnl": 60, "equity_curve": list(range(300))},
                   "research_tournament": {"enabled": True, "pnl": 12, "books": [{"strategy": "trend"}], "recent_trades": list(range(40))},
                   "market_intel": {"health": {"drift": {"ok_markets": 3}}},
                   "validation": {"candidate_total": 9}, "activity_feed": [{"event": "cycle"}]}
        with patch.object(gateway, "request_core", return_value=(200, b'{"ok":true}')), patch.object(gateway, "local_trading_snapshot", return_value=(trading, {"verified": True})):
            code, payload = gateway.compact_status()
        self.assertEqual(code, 200)
        actual = payload["trading"]
        self.assertEqual(actual["total_pnl"], 60)
        self.assertTrue(actual["research_tournament"]["enabled"])
        self.assertEqual(actual["research_lab"]["tested_candidates"], 9)
        self.assertEqual(actual["research_tournament"]["pnl"], 12)
        self.assertEqual(len(actual["research_paper"]["equity_curve"]), 180)
        self.assertEqual(len(actual["research_tournament"]["recent_trades"]), 20)
        self.assertEqual(actual["market_intel"]["health"]["drift"]["ok_markets"], 3)

    def test_missing_research_is_not_fabricated(self):
        with patch.object(gateway, "request_core", return_value=(200, b'{"ok":true}')), patch.object(gateway, "local_trading_snapshot", return_value=({"equity": 10000}, {})):
            _, payload = gateway.compact_status()
        self.assertNotIn("research_tournament", payload["trading"])
