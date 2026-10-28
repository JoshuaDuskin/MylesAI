import unittest

from myles_media import media_request, safe_url
from myles_runtime_v9 import desktop_action_request


class MediaAssistantParsingTests(unittest.TestCase):
    def test_controls_and_followups_are_fast_commands(self):
        self.assertEqual(media_request("Pause the video"), {"kind": "control", "action": "pause"})
        self.assertEqual(media_request("Make it fullscreen"), {"kind": "control", "action": "fullscreen"})
        self.assertEqual(media_request("Play the first episode"), {"kind": "discover", "follow": True, "episode": "first", "play": True})

    def test_discovery_extracts_title_and_playback_intent(self):
        result = media_request("Find South Park and start an episode")
        self.assertEqual(result["title"], "South Park")
        self.assertTrue(result["play"])
        self.assertEqual(media_request("Find a free legal episode")["free"], True)

    def test_only_allowlisted_official_urls_are_navigable(self):
        self.assertTrue(safe_url("https://www.paramountplus.com/shows/south-park/"))
        self.assertTrue(safe_url("https://www.southparkstudios.nu/episodes"))
        self.assertFalse(safe_url("https://example.invalid/watch?token=secret"))
        self.assertFalse(safe_url("http://www.paramountplus.com/"))

    def test_attention_question_uses_native_fast_path(self):
        self.assertEqual(desktop_action_request("What's still open and flashing at me"), {"kind": "windows_attention"})


if __name__ == "__main__":
    unittest.main()
