import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from dashboard_bridge import dashboard_bridge as bridge


class QuantConfigurationRepair(unittest.TestCase):
    def test_saving_paper_limits_preserves_drift_symbols_and_live_lock(self):
        config={'venue':'Drift','chain_id':'solana','starting_equity':10000,'market_settings':{'BTC-PERP':{'enabled':True,'paper_strategy':'mean_reversion'}},'risk':{'max_notional_leverage':1.5},'paper':{'auto_trading_enabled':True}}
        with tempfile.TemporaryDirectory() as folder,patch.object(bridge,'QUANT_CONFIG',Path(folder)/'config.json'):
            bridge.QUANT_CONFIG.write_text(json.dumps(config))
            saved=bridge.save_quant_config({'config':{'venue':'GMX','chain_id':42161,'risk':{'max_notional_leverage':5,'trailing_stop_pct':1,'profile':'aggressive'}}})
        self.assertEqual(saved['venue'],'Drift');self.assertEqual(saved['chain_id'],'solana')
        self.assertEqual(set(saved['market_settings']),{'BTC-PERP','ETH-PERP','SOL-PERP'})
        self.assertEqual(saved['market_settings']['BTC-PERP']['paper_strategy'],'mean_reversion')
        self.assertEqual(saved['risk']['max_notional_leverage'],5)
        self.assertFalse(saved['live_execution']['enabled'])
        self.assertEqual(saved['starting_equity'],10000)

    def test_unsupported_market_is_not_presented_as_executable_drift(self):
        self.assertEqual(bridge.quant_markets({'venue':'Drift'}),['BTC-PERP','ETH-PERP','SOL-PERP'])

if __name__=='__main__':unittest.main()
