import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from dashboard_bridge import dashboard_bridge as bridge


class PredictionControls(unittest.TestCase):
    def test_config_only_changes_paper_entries_and_preserves_ledger(self):
        with tempfile.TemporaryDirectory() as directory, patch.object(bridge, 'ROOT', Path(directory)):
            ledger = Path(directory) / 'data/polymarket_paper_status.json'
            ledger.parent.mkdir()
            ledger.write_text('{"paper_simulation":{"cash_usd":900,"positions":[{"market_id":"keep"}]}}')
            before = ledger.read_bytes()
            for enabled in [False, True]:
                result = bridge.save_prediction_paper_config({'enabled': enabled})
                self.assertEqual(result['paper_enabled'], enabled)
                self.assertTrue(result['live_locked'])
                self.assertEqual(ledger.read_bytes(), before)
                self.assertEqual(json.loads((ledger.parent / 'prediction_paper_config.json').read_text())['enabled'], enabled)

    def test_live_and_invalid_settings_are_rejected(self):
        for payload in [{'enabled': 'true'}, {'enabled': True, 'live': True}, {}, {'enabled': 1}]:
            with self.assertRaises(ValueError):
                bridge.save_prediction_paper_config(payload)
