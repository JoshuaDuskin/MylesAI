import unittest
from unittest.mock import MagicMock, patch
import myles_windows as windows
from myles_runtime_v9 import desktop_action_request

class DesktopControlRepair(unittest.TestCase):
    def test_visible_identified_app_is_open_even_if_foreground_is_denied(self):
        row=self.row(title='Calculator',process='ApplicationFrameHost.exe')
        with patch.object(windows.os,'name','nt'), patch.object(windows,'_matching_visible_windows',return_value=[row]), patch.object(windows,'_activate_window',return_value=False):
            result=windows.launch_app_verified('Calculator')
        self.assertTrue(result.startswith('DESKTOP_APP_LAUNCH_VERIFIED'))
        self.assertIn('FOREGROUND_NOT_GRANTED',result)

    def row(self, handle=100, title='Unsaved document — Notepad', process='notepad.exe'):
        return {'Handle':handle,'Id':42,'MainWindowTitle':title,'ProcessName':process}

    def test_chatgpt_aliases_match_process_not_browser_tab(self):
        actual=self.row(title='A conversation',process='ChatGPT.exe')
        tab=self.row(200,'ChatGPT - Google Chrome','chrome.exe')
        with patch.object(windows,'visible_windows',return_value=[actual,tab]):
            for alias in ['ChatGPT','Chat GPT','chatgpt.exe']:
                self.assertEqual(windows._matching_visible_windows(alias),[actual])
        for text,kind in [('Close chat gpt','close'),('Open ChatGPT','launch'),('Open Chrome','launch'),('Close Notepad','close'),('Minimize the current window','minimize'),('Show me my open windows','windows'),('Switch to another application','windows'),('Close Fortnite','close')]:
            self.assertEqual(desktop_action_request(text)['kind'],kind)

    def operate(self, action='close', matches=None, after=None, force=False, posted=True):
        row=self.row();matches=[row] if matches is None else matches
        native=MagicMock();native.GetForegroundWindow.return_value=100;native.IsWindow.return_value=after!=[];native.IsIconic.return_value=True;native.PostMessageW.return_value=posted
        values=[row] if after is None else after
        with patch.object(windows.os,'name','nt'),patch.object(windows.ctypes,'WinDLL',return_value=native,create=True),patch.object(windows.ctypes,'get_last_error',return_value=5,create=True),patch.object(windows,'visible_windows',side_effect=[[row],[row]]+[values]*10),patch.object(windows,'_matching_visible_windows',side_effect=[matches,[]]),patch.object(windows,'_activate_window',return_value=False):
            result=windows.desktop_operation(action,'Notepad',force=force,timeout=.1)
        return result,native

    def test_graceful_close_requires_observed_disappearance(self):
        result,native=self.operate(after=[])
        self.assertTrue(result['ok']);self.assertEqual(result['state'],'window_closed')
        native.PostMessageW.assert_called_once_with(100,0x0010,0,0)

    def test_unsaved_or_hung_window_is_not_force_terminated(self):
        result,_=self.operate()
        self.assertFalse(result['ok']);self.assertEqual(result['state'],'waiting_on_application')
        self.assertIn('not forced',result['reply'])

    def test_ambiguous_missing_and_permission_failures_do_not_claim_closed(self):
        for matches,state in [([], 'not_found'),([self.row(),self.row(200)],'choice_required')]:
            result,native=self.operate(matches=matches)
            self.assertEqual(result['state'],state);native.PostMessageW.assert_not_called()
        result,_=self.operate(posted=False)
        self.assertFalse(result['ok']);self.assertEqual(result['state'],'permission_denied')

    def test_force_requires_confirmation_and_focus_must_be_verified(self):
        result,native=self.operate(force=True)
        self.assertEqual(result['state'],'confirmation_required');native.PostMessageW.assert_not_called()
        result,_=self.operate(action='focus')
        self.assertFalse(result['ok'])
        self.assertTrue(self.operate(action='minimize')[0]['ok'])
