"""REA capability contract tests run without downloading/launching REA."""
from __future__ import annotations
import json
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from capabilities import rea_analysis as rea


def payload(value: str) -> dict:
    return json.loads(value.removeprefix("TOOL_ERROR: "))


class ReaCapabilityContract(unittest.TestCase):
    def test_success_has_untrusted_evidence_and_limitations(self):
        with patch.object(rea, "_npx", return_value="npx"), \
             patch.object(rea.subprocess, "run", return_value=Mock(
                 returncode=0, stdout='{"modules":2}')):
            data = payload(rea._run(["doctor", "--json"], 30))
            self.assertTrue(data["ok"])
            self.assertEqual(data["outcome"], "observed")
            self.assertTrue(data["provenance"]["untrusted_content"])
            self.assertIn("private model weights", data["limitations"][0])

    def test_analysis_provider_failure_preserves_exit_code(self):
        with patch.object(rea, "_npx", return_value="npx"), \
             patch.object(rea.subprocess, "run", return_value=Mock(
                 returncode=12, stdout="provider unavailable")):
            value = rea._run(["doctor"], 30)
            self.assertTrue(value.startswith("TOOL_ERROR: "))
            data = payload(value)
            self.assertFalse(data["ok"])
            self.assertEqual(data["outcome"], "provider_or_analysis_failure")
            self.assertEqual(data["exit_code"], 12)

    def test_timeout_is_explicit_unverified_outcome(self):
        timeout = subprocess.TimeoutExpired(["npx", "rea-agents"], 30, output=b"partial metadata")
        with patch.object(rea, "_npx", return_value="npx"), \
             patch.object(rea.subprocess, "run", side_effect=timeout):
            data = payload(rea._run(["doctor"], 30))
            self.assertFalse(data["ok"])
            self.assertEqual(data["outcome"], "timeout")
            self.assertIn("partial metadata", data["output"])

    def test_missing_executable_is_not_success(self):
        with patch.object(rea, "_npx", side_effect=RuntimeError("no npx")):
            data = payload(rea._run(["doctor"], 30))
            self.assertFalse(data["ok"])
            self.assertEqual(data["outcome"], "unavailable")

    def test_protected_path_never_invokes_rea(self):
        with tempfile.TemporaryDirectory(prefix="pinetree_fixture_") as folder:
            with patch.object(rea, "_run") as execute:
                result = rea.rea_analyze_javascript_application(folder)
                self.assertTrue(result.startswith("REFUSED_PINETREE"))
                execute.assert_not_called()

    def test_missing_path_not_claimed_observed(self):
        with patch.object(rea, "_run") as execute:
            result = rea.rea_analyze_javascript_application(
                "path_not_exist_293849_this_should_not_exist")
            self.assertIn("does not exist", result)
            execute.assert_not_called()


if __name__ == "__main__":
    unittest.main()
