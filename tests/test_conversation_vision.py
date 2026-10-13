from __future__ import annotations
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import myles_conversation as c
import myles_visual_verify as v


class ContextTests(unittest.TestCase):
    def test_keeps_recent_and_relevant_older_topic(self):
        rows = []
        def add(role, text):
            rows.append({"role":role,"content":text})
        add("user","The access point uses a switch for ethernet uplink.")
        add("assistant","Yes, that powers and links the Wi-Fi access point.")
        for n in range(30):
            add("user", f"Unrelated quiz turn {n} about weather")
            add("assistant", f"Unrelated generic response {n}")
        add("user","Can you remind me how the access point connects to the switch?")
        history=c.select_history(rows, "Can you remind me how the access point connects to the switch?",
                                 recent=8, max_chars=11000)
        joined="\n".join(x["content"] for x in history)
        self.assertIn("access point uses a switch",joined)
        self.assertIn("Older conversation context",joined)
        self.assertLessEqual(sum(len(x["content"]) for x in history),11000)
        self.assertEqual(history[-1]["role"],"assistant")

    def test_no_fabricated_missing_history(self):
        self.assertEqual(c.select_history([], "What was that?"),[])
        entries=[{"role":"tool","content":"secret"},
                 {"role":"assistant","content":"hello"},
                 {"role":"user","content":"current"}]
        self.assertEqual(c.select_history(entries,"current"),[{"role":"assistant","content":"hello"}])

    def test_failure_overrules_unverified_completion(self):
        self.assertIn("couldn't verify", c.safe_tool_reply(
            "Done! I clicked the button.",any_failure=True,started_job=False))
        self.assertEqual(c.safe_tool_reply(
            "I couldn't complete it.",any_failure=True,started_job=False),
            "I couldn't complete it.")
        self.assertEqual(c.safe_tool_reply(
            "Hi.",any_failure=False,started_job=False),"Hi.")


class VisionTests(unittest.TestCase):
    def _pair(self):
        root=tempfile.TemporaryDirectory()
        base=Path(root.name)
        job="fixture_job"
        w=base/job
        w.mkdir()
        one=w/"before.png";two=w/"after.png"
        one.write_bytes(b"\x89PNG\r\n\x1a\n"+b"a"*100)
        two.write_bytes(b"\x89PNG\r\n\x1a\n"+b"b"*100)
        mk=lambda p: "MYLES_DESKTOP_IMAGE "+json.dumps({"path":str(p)})
        return root,base,mk(one),mk(two),two

    def test_high_confidence_specific_local_visual_verification(self):
        t,base,pre,post,_=self._pair()
        try:
            def local(*args,**kwargs):
                self.assertEqual(len(args[1][-1]["images"]),2)
                self.assertTrue(kwargs["json_mode"])
                return {"message":{"content":json.dumps({
                  "verified":True,"confidence":"high",
                  "observation":"The settings panel is open and showing the requested option."})}}
            with patch.object(v,"WORKSPACES",base),patch("myles_model_runtime.model_health_dict",return_value={"supports_vision":True}):
                good,report=v.verify_desktop_effect("fixture_job","Open settings",pre,post,model_callable=local)
            self.assertTrue(good,report)
        finally:t.cleanup()

    def test_identical_screenshot_cannot_pass(self):
        t,base,pre,post,path=self._pair()
        try:
            path.write_bytes((base/"fixture_job"/"before.png").read_bytes())
            with patch.object(v,"WORKSPACES",base):
                good,report=v.verify_desktop_effect("fixture_job","Open settings",pre,post)
            self.assertFalse(good)
            self.assertIn("identical",report)
        finally:t.cleanup()

    def test_low_confidence_or_missing_vision_fails(self):
        t,base,pre,post,_=self._pair()
        try:
            local=lambda *a,**k: {"message":{"content":json.dumps({
                "verified":True,"confidence":"low","observation":"Maybe it opened"})}}
            with patch.object(v,"WORKSPACES",base),patch("myles_model_runtime.model_health_dict",return_value={"supports_vision":True}):
                result,detail=v.verify_desktop_effect("fixture_job","Open settings",pre,post,model_callable=local)
                self.assertFalse(result)
            with patch.object(v,"WORKSPACES",base),patch("myles_model_runtime.model_health_dict",return_value={"supports_vision":False}):
                result,detail=v.verify_desktop_effect("fixture_job","Open settings",pre,post,model_callable=local)
                self.assertFalse(result)
        finally:t.cleanup()

    def test_external_image_path_blocked(self):
        t,base,pre,post,_=self._pair()
        try:
            with patch.object(v,"WORKSPACES",base):
                good,detail=v.verify_desktop_effect("otherjob","Do something",pre,post)
            self.assertFalse(good)
            self.assertIn("not a valid",detail)
        finally:t.cleanup()


if __name__=="__main__":
    unittest.main()
