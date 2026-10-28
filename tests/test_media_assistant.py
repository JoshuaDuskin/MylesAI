import unittest
from unittest.mock import patch

from myles_media import media_request, safe_url
from myles_runtime_v9 import desktop_action_request
import myles_core as core


class MediaAssistantParsingTests(unittest.TestCase):
    def test_controls_and_followups_are_fast_commands(self):
        self.assertEqual(media_request("Pause the video"), {"kind": "control", "action": "pause"})
        self.assertEqual(media_request("Pause video"), {"kind": "control", "action": "pause"})
        self.assertEqual(media_request("Play"), {"kind": "control", "action": "resume"})
        self.assertEqual(media_request("Play video"), {"kind": "control", "action": "resume"})
        self.assertEqual(media_request("It's still playing"), {"kind": "control", "action": "status"})
        self.assertEqual(media_request("Make it fullscreen"), {"kind": "control", "action": "fullscreen"})
        self.assertEqual(media_request("Make YouTube video full screen"), {"kind": "control", "action": "fullscreen"})
        self.assertEqual(media_request("Go full screen"), {"kind": "control", "action": "fullscreen"})
        self.assertEqual(media_request("Take it out of full screen"), {"kind": "control", "action": "exit_fullscreen"})
        self.assertEqual(media_request("Skip the ad"), {"kind": "control", "action": "skip_ad"})
        self.assertEqual(media_request("Play the first episode"), {"kind": "discover", "follow": True, "episode": "first", "play": True})
        self.assertEqual(media_request("Play the song"), {"kind": "youtube_follow", "selection": "first", "play": True})

    def test_discovery_extracts_title_and_playback_intent(self):
        result = media_request("Find South Park and start an episode")
        self.assertEqual(result["title"], "South Park")
        self.assertTrue(result["play"])
        self.assertEqual(media_request("Find a free legal episode")["free"], True)

    def test_natural_provider_and_web_search_requests_keep_the_title(self):
        self.assertEqual(media_request("Open YouTube and play a video called K-pop Demon hunters"),
                         {"kind": "youtube", "title": "K-pop Demon hunters", "play": True})
        self.assertEqual(media_request("Watch K-pop Demon Hunters on Netflix"),
                         {"kind": "service_search", "service": "netflix", "title": "K-pop Demon Hunters", "play": True})
        self.assertEqual(media_request("Open Hulu and watch South Park"),
                         {"kind": "service_search", "service": "hulu", "title": "South Park", "play": True})
        self.assertEqual(media_request("Find an article about Windows 11 updates"),
                         {"kind": "web_search", "title": "Windows 11 updates"})

    def test_open_youtube_latest_phrases_bypass_generic_research(self):
        self.assertEqual(media_request("Open why files on YouTube"),
                         {"kind": "youtube", "title": "why files", "play": True})
        self.assertEqual(media_request("Open newest why files video on YouTube"),
                         {"kind": "youtube", "title": "why files", "play": True, "selection": "latest"})
        self.assertEqual(media_request("Open the latest video from Why Files on YouTube"),
                         {"kind": "youtube", "title": "Why Files", "play": True, "selection": "latest"})

    def test_only_allowlisted_official_urls_are_navigable(self):
        self.assertTrue(safe_url("https://www.paramountplus.com/shows/south-park/"))
        self.assertTrue(safe_url("https://www.southparkstudios.nu/episodes"))
        self.assertTrue(safe_url("https://www.google.com/search?q=fortnite"))
        self.assertFalse(safe_url("https://example.invalid/watch?token=secret"))
        self.assertFalse(safe_url("http://www.paramountplus.com/"))

    def test_attention_question_uses_native_fast_path(self):
        self.assertEqual(desktop_action_request("What's still open and flashing at me"), {"kind": "windows_attention"})

    def test_owner_media_request_precedes_app_launch_and_game_pause(self):
        class FakeAssistant:
            def handle(self, request):
                self.request = request
                return {"ok": True, "reply": "MEDIA_OK"}
        fake = FakeAssistant()
        with patch.object(core, "game_is_active", return_value=True), \
             patch.object(core, "add_message", return_value=1), \
             patch("myles_media.assistant", return_value=fake):
            result = core.handle_owner_message("Open YouTube and play a video called K-pop Demon hunters", "dashboard")
        self.assertEqual(result["reply"], "MEDIA_OK")
        self.assertEqual(fake.request["kind"], "youtube")

    def test_browser_window_fullscreen_is_a_verified_desktop_action(self):
        self.assertEqual(desktop_action_request("Put Microsoft edge in full screen as well"),
                         {"kind": "maximize", "target": "Microsoft edge"})
        self.assertEqual(desktop_action_request("Maximize Chrome"),
                         {"kind": "maximize", "target": "Chrome"})
        self.assertEqual(desktop_action_request("Make chrome full screen"),
                         {"kind": "maximize", "target": "chrome"})


if __name__ == "__main__":
    unittest.main()
