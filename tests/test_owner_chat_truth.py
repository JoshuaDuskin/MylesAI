"""Phone-chat regression cases taken from observed owner screenshot.

Tests use mocked local job rows and model responses; they are not claimed
as live Windows or REA black-box studies of third-party assistants.
"""
from __future__ import annotations

import unittest
from unittest.mock import patch

import myles_core as core
from myles_conversation import unfinished_model_reply


CLEANUP={"id":"job-cleanup","source":"dashboard","prompt":"Perform the cleanup job",
         "state":"failed","phase":"verification","error":"no verified output stored"}
RUNNING={"id":"job-running","source":"dashboard","prompt":"Review REA research evidence",
         "state":"running","phase":"scanning","runner_pid":777}
OTHER={"id":"job-other","source":"dashboard","prompt":"Change UI colors",
       "state":"completed","phase":"verified","result":"Theme changed and validated"}
CONTINUOUS={"id":"job-cycle","source":"continuous","prompt":"automated cycle",
            "state":"running","phase":"exploring"}


def truth(item):
    return {**item,"truth_state":item["state"],"live_worker":item["state"]=="running",
            "stall_reasons":[]}


class PhoneChatTruthTests(unittest.TestCase):
    def test_screenshot_prompts_are_reports_not_new_tasks(self):
        for text in (
            "Give me report",
            "With the background job stupid",
            "Let me know when you're done",
            "Give me a report on that cleanup job",
            "How is the previous job?",
        ):
            with self.subTest(text=text):
                self.assertTrue(core.owner_report_request(text))
        for text in ("Give me a new website report generator",
                     "Run REA analysis of software", "Please fix Myles",
                     "Build a cleanup job", "What is RJ45?"):
            self.assertFalse(core.owner_report_request(text))

    def test_latest_failed_job_explains_failure_without_guessing(self):
        with patch.object(core,"list_jobs",return_value=[CLEANUP,OTHER]), \
             patch.object(core,"active_job",return_value=None), \
             patch.object(core,"job_truth",side_effect=truth):
            report=core.owner_job_report("Give me report")
            self.assertIn("State: FAILED",report)
            self.assertIn("no verified output stored",report)
            self.assertIn("verification",report)
            self.assertNotIn("Theme changed",report)

    def test_specific_cleanup_followup_does_not_report_wrong_job(self):
        with patch.object(core,"list_jobs",return_value=[OTHER]), \
             patch.object(core,"active_job",return_value=None), \
             patch.object(core,"status_text",return_value="Nothing running"):
            answer=core.owner_job_report("With the cleanup job stupid")
        self.assertIn("couldn't find a recorded cleanup job",answer)
        self.assertNotIn("Theme changed",answer)

    def test_active_job_reports_only_observed_running(self):
        with patch.object(core,"list_jobs",return_value=[RUNNING,CLEANUP]), \
             patch.object(core,"active_job",return_value=RUNNING), \
             patch.object(core,"job_truth",side_effect=truth):
            report=core.owner_job_report("Give me report")
            self.assertIn("State: RUNNING",report)
            self.assertIn("No completion has been verified",report)
            self.assertIn("Worker alive: True",report)

    def test_stalled_job_does_not_claim_normal_progress(self):
        stalled={**RUNNING,"truth_state":"stalled","live_worker":False,
                 "stall_reasons":["worker process is not alive"]}
        with patch.object(core,"list_jobs",return_value=[RUNNING]), \
             patch.object(core,"active_job",return_value=RUNNING), \
             patch.object(core,"job_truth",return_value=stalled):
            report=core.owner_job_report("Give me report")
            self.assertIn("STALLED",report)
            self.assertIn("worker process is not alive",report)
            self.assertNotIn("running normally",report)

    def test_missing_jobs_is_clear_instead_of_inventing_a_cleanup_job(self):
        with patch.object(core,"list_jobs",return_value=[]), \
             patch.object(core,"active_job",return_value=None), \
             patch.object(core,"status_text",return_value="No owner task is currently running."):
            self.assertIn("No owner task",core.owner_job_report("Give me report"))

    def test_partial_sentences_are_never_final_answers(self):
        cases=(
            {"content":"The previous cleanup job didn"}, 
            {"content":"I understand you want me to let you know when that cleanup job"},
        )
        for case in cases:
            with self.subTest(text=case["content"]):
                self.assertTrue(unfinished_model_reply({"done_reason":"stop"},case["content"]))
        self.assertTrue(unfinished_model_reply({"done_reason":"length"},"Complete-looking text."))
        self.assertFalse(unfinished_model_reply({"done_reason":"stop"},"The task failed verification."))
        self.assertFalse(unfinished_model_reply({"done_reason":"stop"},"I'm here."))

    def test_short_circuit_phone_report_without_model_or_new_task(self):
        rows=[CLEANUP]
        output=[]
        def record(*args):
            output.append(args)
            return len(output)
        with patch.object(core,"game_is_active",return_value=False), \
             patch.object(core,"list_jobs",return_value=rows), \
             patch.object(core,"active_job",return_value=None), \
             patch.object(core,"job_truth",side_effect=truth), \
             patch.object(core,"add_message",side_effect=record), \
             patch.object(core,"_start_task") as start, \
             patch.object(core,"model_chat") as model:
            result=core.handle_owner_message("Give me report","dashboard")
        self.assertEqual(result["kind"],"conversation")
        self.assertIn("State: FAILED",result["reply"])
        self.assertEqual(len(output),2)
        start.assert_not_called()
        model.assert_not_called()

    def test_model_cutoff_never_claims_completion(self):
        with patch.object(core,"recent_messages",return_value=[]), \
             patch.object(core,"load_config",return_value={}), \
             patch.object(core,"_conversation_runtime_context",return_value="No task"), \
             patch.object(core,"_conversation_call",return_value={
                  "done_reason":"stop",
                  "message":{"content":"The previous cleanup job didn", "tool_calls":[]}}), \
             patch.object(core,"owner_job_report",return_value="Job failed verification."), \
             patch.object(core,"_conversation_tool") as tool:
            reply,job=core._conversation_agent_turn("Tell me what happened to the cleanup job","test")
        self.assertEqual(job,None)
        self.assertEqual(reply,"Job failed verification.")
        tool.assert_not_called()

    def test_continuous_status_does_not_claim_healthy_when_stalled(self):
        with patch.object(core,"active_job",return_value=CONTINUOUS), \
             patch.object(core,"load_config",return_value={"light_mode":False}), \
             patch.object(core,"list_jobs",return_value=[CONTINUOUS]), \
             patch.object(core,"job_truth",return_value={
                 **CONTINUOUS,"truth_state":"stalled","live_worker":False,
                 "stall_reasons":["heartbeat missing"]}):
            report=core.status_text()
        self.assertIn("STALLED",report)
        self.assertIn("heartbeat missing",report)
        self.assertNotIn("running normally",report)


if __name__=="__main__":
    unittest.main()
