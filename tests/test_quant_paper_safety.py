"""Static safety boundaries for Quant's existing automatic paper logic.

CI's separate node --self-test exercises the executable logic. These explicit
contracts prevent accidental reintroduction of shadow-order or halt bypass.
"""
from pathlib import Path
import unittest

SCRIPT=(Path(__file__).resolve().parents[1]/"quant"/"quant_service.mjs").read_text(encoding="utf-8")


class QuantPaperSafetyTests(unittest.TestCase):
    def test_shadow_hypotheses_never_enter_actual_paper_positions(self):
        self.assertIn("source:'research_shadow_only',research_signal:shadowSignal",SCRIPT)
        self.assertIn("signal:0,source:'research_shadow_only'",SCRIPT)
        self.assertIn("const eligiblePaperCandidates=strictEligiblePaperCandidates",SCRIPT)
        self.assertNotIn("source:'research_shadow_candidate'",SCRIPT)
        self.assertIn("research_signal:choice.source==='research_shadow_only'",SCRIPT)

    def test_halts_not_reset_by_research_cycles(self):
        self.assertNotIn("research_shadow_recovery",SCRIPT)
        self.assertIn("const persistentHalt=state.halt_reason==='max_drawdown_limit'",SCRIPT)
        self.assertIn("if(!persistentHalt){state.halted=false;state.halt_reason=null;}",SCRIPT)
        self.assertIn("config.paper.emergency_stop",SCRIPT)

    def test_forward_gate_demands_observed_positive_windows(self):
        self.assertIn("n(r?.walk_forward?.total_windows,0)>=2",SCRIPT)
        self.assertIn("n(r?.walk_forward?.positive_windows,0)>=1",SCRIPT)
        self.assertIn("return row.validation?.pass===true || forwardCandidate(row,config)",SCRIPT)
        self.assertNotIn("if(config.paper?.require_candidate_evidence===false)return true",SCRIPT)

    def test_existing_paper_history_and_owner_live_controls_preserved(self):
        self.assertIn("quant_paper_state_v3.json",SCRIPT)
        self.assertIn("live_execution: {",SCRIPT)
        self.assertIn("enabled: false",SCRIPT)
        self.assertIn("signing_enabled: false",SCRIPT)


if __name__=="__main__":
    unittest.main()
