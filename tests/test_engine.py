from contextlib import ExitStack
import os
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import MagicMock, Mock, patch

from core.config import Config
import core.engine as engine_module
from core.engine import AutoSkipEngine, Key, fast_key_press, fast_mouse_click


class EndLoop(Exception):
    pass


class EngineTests(unittest.TestCase):
    def setUp(self):
        self.stack = ExitStack()
        self.addCleanup(self.stack.close)
        temp = self.stack.enter_context(tempfile.TemporaryDirectory())
        self.stack.enter_context(patch.dict(os.environ, {}, clear=True))
        self.stack.enter_context(patch('core.config.get_screen_resolution', return_value=(1920, 1080)))
        self.config = Config(str(Path(temp) / '.env'))
        self.engine = AutoSkipEngine(self.config)
        self.engine.on_log = lambda *args: None
        self.native = self.stack.enter_context(patch.object(engine_module, 'user32', Mock()))
        self.native.MapVirtualKeyW.return_value = 33
        self.focus = self.stack.enter_context(patch.object(engine_module.win32gui, 'GetForegroundWindow', return_value=123))
        self.move = self.stack.enter_context(patch.object(engine_module.pyautogui, 'moveTo'))

    def run_one_cycle(self, narrative=lambda *args: False, dialogue=lambda *args: False,
                      choice=lambda *args: None):
        def sleep_once(seconds):
            if seconds >= 0.02 or seconds == 0.002:
                raise EndLoop

        self.engine.status = 'running'
        with patch.object(engine_module, 'get_genshin_window_info', return_value=(True, 123, 'Genshin Impact', 300, 200, 1920, 1080, True)), \
             patch.object(engine_module, 'sleep', side_effect=sleep_once), \
             patch.object(self.engine, 'is_narrative_screen', side_effect=narrative), \
             patch.object(self.engine, 'is_dialogue_playing', side_effect=dialogue), \
             patch.object(self.engine, 'is_dialogue_option_available', side_effect=choice):
            with self.assertRaises(EndLoop):
                self.engine._loop()

    def test_manual_resolution_keeps_client_origin(self):
        self.config.auto_window_mode = False
        sampled = []
        self.run_one_cycle(narrative=lambda *args: sampled.append(args) or False)
        self.assertEqual(sampled[0], (300, 200, 1920, 1080))

    def test_pause_during_narrative_detection_prevents_input(self):
        def detect(*args):
            self.engine.pause()
            return True
        self.run_one_cycle(narrative=detect)
        self.native.keybd_event.assert_not_called()
        self.native.mouse_event.assert_not_called()

    def test_focus_loss_during_detection_prevents_input(self):
        def detect(*args):
            self.focus.return_value = 456
            return True
        self.run_one_cycle(dialogue=detect)
        self.native.keybd_event.assert_not_called()
        self.native.mouse_event.assert_not_called()

    def test_pause_during_burst_stops_remaining_keys_and_clicks(self):
        def press(*args):
            if args[2] == engine_module.KEYEVENTF_KEYDOWN:
                self.engine.pause()
        self.native.keybd_event.side_effect = press
        self.engine.status = 'running'
        count = self.engine._execute_spam_burst('f', 5, 0, True, hwnd=123)
        self.assertEqual(count, 1)
        self.assertEqual(self.native.keybd_event.call_count, 2)
        self.native.mouse_event.assert_not_called()

    def test_stop_during_burst_stops_remaining_keys_and_clicks(self):
        def press(*args):
            if args[2] == engine_module.KEYEVENTF_KEYDOWN:
                self.engine.stop()
        self.native.keybd_event.side_effect = press
        self.engine.status = 'running'
        count = self.engine._execute_spam_burst('f', 5, 0, True, hwnd=123)
        self.assertEqual(count, 1)
        self.assertEqual(self.native.keybd_event.call_count, 2)
        self.native.mouse_event.assert_not_called()

    def test_focus_loss_after_key_prevents_combo_click(self):
        def press(*args):
            if args[2] == engine_module.KEYEVENTF_KEYUP:
                self.focus.return_value = 456
        self.native.keybd_event.side_effect = press
        self.engine.status = 'running'
        self.assertEqual(self.engine._execute_spam_burst('f', 5, 0, True, hwnd=123), 1)
        self.native.mouse_event.assert_not_called()

    def test_choice_click_targets_answer_once_without_confirm_burst(self):
        self.engine.status = 'running'
        count = self.engine._execute_spam_burst('f', 5, 0, True, hwnd=123, click_position=(1351, 808))
        self.assertEqual(count, 1)
        self.move.assert_called_once_with(1351, 808, duration=0)
        self.native.keybd_event.assert_not_called()
        self.assertEqual(self.native.mouse_event.call_count, 2)

    def test_focus_loss_after_targeting_prevents_choice_click(self):
        self.engine.status = 'running'
        self.move.side_effect = lambda *args, **kwargs: setattr(self.focus, 'return_value', 456)
        count = self.engine._execute_spam_burst('f', 5, 0, True, hwnd=123, click_position=(1351, 808))
        self.assertEqual(count, 0)
        self.native.mouse_event.assert_not_called()

    def test_choice_detector_returns_lowest_matching_answer_position(self):
        def sample(x, y):
            return (230, 230, 230) if (x, y) in {(1301, 808), (1301, 790)} else (40, 40, 40)
        with patch.object(engine_module, 'pixel', side_effect=sample):
            position = self.engine.is_dialogue_option_available(1200, 700, 1301, 808, 790)
        self.assertEqual(position, (1351, 808))

    def test_loading_screen_has_no_answer_target(self):
        with patch.object(engine_module, 'pixel', return_value=(255, 255, 255)):
            self.assertIsNone(self.engine.is_dialogue_option_available(1200, 700, 1301, 808, 790))

    def test_choice_detector_prefers_midpoint_over_higher_answer(self):
        def sample(x, y):
            return (230, 230, 230) if (x, y) in {(1301, 799), (1301, 790)} else (40, 40, 40)
        with patch.object(engine_module, 'pixel', side_effect=sample):
            self.assertEqual(
                self.engine.is_dialogue_option_available(1200, 700, 1301, 808, 790),
                (1351, 799),
            )

    def test_extreme_honors_one_press_per_burst(self):
        self.config.spam_mode, self.config.burst_count = 'extreme', 1
        self.assertEqual(self.engine._get_mode_params()[1], 1)

    def test_stopped_engine_cannot_report_running_without_worker(self):
        self.engine.stop()
        self.engine.start()
        self.assertEqual(self.engine.status, 'stopped')

    def test_f12_stops_even_during_hotkey_recording(self):
        self.engine.recording_hotkey_for = 'start'
        self.engine._on_key_press(Key.f12)
        self.assertEqual(self.engine.status, 'stopped')
        self.assertEqual(self.config.hotkey_start, 'f8')

    def test_conflicting_recorded_key_reports_error_without_killing_listener(self):
        recorded = []
        self.engine.on_hotkey_recorded = lambda *args: recorded.append(args)
        self.engine.recording_hotkey_for = 'pause'
        self.engine._on_key_press(Key.f8)
        self.assertEqual(self.config.hotkey_pause, 'f9')
        self.assertEqual(recorded[0][0], 'pause')
        self.assertTrue(recorded[0][1].startswith('error:'))

    def test_recording_blocks_generated_input(self):
        self.engine.status = 'running'
        self.engine.recording_hotkey_for = 'pause'
        count = self.engine._execute_spam_burst('f', 2, 0, False, hwnd=123)
        self.assertEqual(count, 0)
        self.native.keybd_event.assert_not_called()

    def test_keyboard_listener_filters_injected_events(self):
        with patch.object(engine_module.threading, 'Thread'), \
             patch.object(engine_module, 'KeyListener') as listener, \
             patch.object(engine_module, 'MouseListener'):
            self.engine.run_in_background()
        event_filter = listener.call_args.kwargs.get('win32_event_filter')
        self.assertIsNotNone(event_filter)
        self.assertFalse(event_filter(0x100, SimpleNamespace(flags=0x10)))
        self.assertTrue(event_filter(0x100, SimpleNamespace(flags=0)))

    def test_key_is_released_if_hold_is_interrupted(self):
        with patch.object(engine_module, 'sleep', side_effect=OSError('interrupted')):
            with self.assertRaises(OSError):
                fast_key_press('f')
        self.assertEqual(self.native.keybd_event.call_args.args[2], engine_module.KEYEVENTF_KEYUP)

    def test_mouse_is_released_if_hold_is_interrupted(self):
        with patch.object(engine_module, 'sleep', side_effect=OSError('interrupted')):
            with self.assertRaises(OSError):
                fast_mouse_click()
        self.assertEqual(self.native.mouse_event.call_args.args[0], engine_module.MOUSEEVENTF_LEFTUP)

    def test_unsupported_key_is_rejected_without_sending_f(self):
        with self.assertRaises(ValueError):
            fast_key_press('tab', hold_sec=0)
        self.native.keybd_event.assert_not_called()


class WindowIdentityTests(unittest.TestCase):
    def test_failed_image_query_closes_process_handle(self):
        handle = MagicMock()
        handle.__int__.return_value = 123
        with patch.object(engine_module.win32api, 'OpenProcess', return_value=handle), \
             patch.object(engine_module.kernel32, 'QueryFullProcessImageNameW', return_value=False):
            with self.assertRaises(OSError):
                engine_module.get_process_executable(321)
        handle.Close.assert_called_once_with()

    def test_open_process_access_denied_rejects_window(self):
        with patch.object(engine_module.win32gui, 'IsWindow', return_value=True), \
             patch.object(engine_module.win32gui, 'IsWindowVisible', return_value=True), \
             patch.object(engine_module.win32process, 'GetWindowThreadProcessId', return_value=(1, os.getpid() + 1)), \
             patch.object(engine_module.win32api, 'OpenProcess', side_effect=PermissionError('access denied')):
            self.assertFalse(engine_module.is_real_genshin_window(123))

    def test_browser_title_does_not_make_it_a_game(self):
        with patch.object(engine_module.win32gui, 'IsWindow', return_value=True), \
             patch.object(engine_module.win32gui, 'IsWindowVisible', return_value=True), \
             patch.object(engine_module.win32gui, 'GetWindowText', return_value='Genshin Impact guide - Google Chrome'), \
             patch.object(engine_module.win32process, 'GetWindowThreadProcessId', return_value=(1, os.getpid() + 1)), \
             patch.object(engine_module, 'get_process_executable', return_value='chrome.exe', create=True):
            self.assertFalse(engine_module.is_real_genshin_window(123))

    def test_game_executable_is_accepted(self):
        for name in ('GenshinImpact.exe', 'YuanShen.exe'):
            with self.subTest(name=name), \
                 patch.object(engine_module.win32gui, 'IsWindow', return_value=True), \
                 patch.object(engine_module.win32gui, 'IsWindowVisible', return_value=True), \
                 patch.object(engine_module.win32gui, 'GetWindowText', return_value='Genshin Impact'), \
                 patch.object(engine_module.win32process, 'GetWindowThreadProcessId', return_value=(1, os.getpid() + 1)), \
                 patch.object(engine_module, 'get_process_executable', return_value=name, create=True):
                self.assertTrue(engine_module.is_real_genshin_window(123))

    def test_failed_process_lookup_denies_input(self):
        with patch.object(engine_module.win32gui, 'IsWindow', return_value=True), \
             patch.object(engine_module.win32gui, 'IsWindowVisible', return_value=True), \
             patch.object(engine_module.win32gui, 'GetWindowText', return_value='Genshin Impact'), \
             patch.object(engine_module.win32process, 'GetWindowThreadProcessId', side_effect=OSError('access denied')):
            self.assertFalse(engine_module.is_real_genshin_window(123))


if __name__ == '__main__':
    unittest.main()
