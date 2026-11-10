from contextlib import ExitStack
import os
from pathlib import Path
import queue
import tempfile
from types import MethodType, SimpleNamespace
import unittest
from unittest.mock import Mock, patch

from core.config import Config
from core.engine import AutoSkipEngine
from gui import AutoSkipGUI


class GuiCallbacksTests(unittest.TestCase):
    def setUp(self):
        self.stack = ExitStack()
        self.addCleanup(self.stack.close)
        temp = self.stack.enter_context(tempfile.TemporaryDirectory())
        self.stack.enter_context(patch.dict(os.environ, {}, clear=True))
        self.config = Config(str(Path(temp) / '.env'))
        self.engine = AutoSkipEngine(self.config)
        self.engine.on_log = lambda *args: None
        self.gui = SimpleNamespace(
            config=self.config, engine=self.engine, recording_target=None,
            _closing=False, event_queue=queue.Queue(), _on_close=Mock(),
            _append_log=Mock(), _update_status_ui=Mock(), _update_stats_ui=Mock(),
            _update_window_ui=Mock(), _handle_hotkey_recorded=Mock(), after=Mock(),
            key_combo=Mock(), burst_combo=Mock(), _refresh_hotkey_buttons=Mock(),
            btn_bind_start=Mock(), btn_bind_pause=Mock(),
        )
        self.gui._save_config = lambda **kwargs: AutoSkipGUI._save_config(self.gui, **kwargs)
        self.gui._process_events = MethodType(AutoSkipGUI._process_events, self.gui)

    def test_stopped_event_closes_gui_without_scheduling_more_events(self):
        self.gui.event_queue.put(('status', 'stopped'))
        self.gui.event_queue.put(('log', ('late log', 'info')))
        AutoSkipGUI._process_events(self.gui)
        self.gui._on_close.assert_called_once_with()
        self.gui.after.assert_not_called()
        self.gui._append_log.assert_not_called()

    def test_rejected_confirm_change_restores_display_and_reports_error(self):
        self.config.save(hotkey_pause='e')
        AutoSkipGUI._on_key_change(self.gui, 'E')
        self.assertEqual(self.config.confirm_button, 'f')
        self.gui.key_combo.set.assert_called_once_with('F')
        self.assertEqual(self.gui._append_log.call_args.args[1], 'warning')

    def test_invalid_burst_restores_display_and_reports_error(self):
        for value in ('0x', '1000000x', 'oops'):
            with self.subTest(value=value):
                AutoSkipGUI._on_burst_change(self.gui, value)
                self.assertEqual(self.config.burst_count, 2)
                self.gui.burst_combo.set.assert_called_with('2x')
                self.assertEqual(self.gui._append_log.call_args.args[1], 'warning')

    def test_starting_hotkey_recording_pauses_engine(self):
        self.engine.status = 'running'
        AutoSkipGUI._on_bind_start_click(self.gui)
        self.assertEqual(self.engine.status, 'paused')
        self.assertEqual(self.engine.recording_hotkey_for, 'start')

    def test_recording_error_is_reported_as_warning(self):
        AutoSkipGUI._handle_hotkey_recorded(self.gui, 'pause', 'error:duplicate key')
        self.assertEqual(self.gui._append_log.call_args.args[1], 'warning')
        self.assertIn('duplicate key', self.gui._append_log.call_args.args[0])

    def test_close_returns_without_system_exit_and_is_idempotent(self):
        gui = SimpleNamespace(_closing=False, engine=Mock(), destroy=Mock())
        AutoSkipGUI._on_close(gui)
        AutoSkipGUI._on_close(gui)
        gui.engine.stop.assert_called_once_with()
        gui.destroy.assert_called_once_with()


if __name__ == '__main__':
    unittest.main()
