import os
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import tempfile
import threading
import unittest
from unittest.mock import patch

from dotenv import dotenv_values, set_key

from core.config import Config


class ConfigTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.env_path = Path(self.temp.name) / '.env'
        self.env_path.write_text('', encoding='utf-8')
        self.env = patch.dict(os.environ, {}, clear=True)
        self.env.start()
        self.addCleanup(self.env.stop)
        screen = patch('core.config.get_screen_resolution', return_value=(1920, 1080))
        screen.start()
        self.addCleanup(screen.stop)

    def load(self, text=''):
        self.env_path.write_text(text, encoding='utf-8')
        return Config(str(self.env_path))

    def test_invalid_dimensions_and_burst_fall_back_with_warnings(self):
        config = self.load('WIDTH=0\nHEIGHT=-1\nBURST_COUNT=1000000\n')
        self.assertEqual((config.width, config.height, config.burst_count), (1920, 1080, 2))
        self.assertTrue(config.warnings)

    def test_unsupported_confirm_falls_back_with_warning(self):
        config = self.load('CONFIRM_BUTTON=tab\n')
        self.assertEqual(config.confirm_button, 'f')
        self.assertTrue(config.warnings)

    def test_conflicting_loaded_hotkeys_reset_to_defaults(self):
        for text in ('HOTKEY_START=f9\n', 'HOTKEY_START=f12\n',
                     'HOTKEY_PAUSE=space\n', 'HOTKEY_START=f\n'):
            with self.subTest(text=text):
                config = self.load(text)
                self.assertEqual((config.hotkey_start, config.hotkey_pause), ('f8', 'f9'))
                self.assertTrue(config.warnings)

    def test_invalid_save_does_not_change_memory_or_file(self):
        config = self.load()
        original = self.env_path.read_bytes()
        for change in ({'width': 0}, {'burst_count': 0}, {'burst_count': 6},
                       {'confirm_button': 'tab'}, {'hotkey_start': 'f9'},
                       {'hotkey_start': 'f12'}, {'hotkey_pause': 'space'},
                       {'hotkey_start': 'not_a_key'}):
            with self.subTest(change=change):
                with self.assertRaises(ValueError):
                    config.save(**change)
                self.assertEqual(self.env_path.read_bytes(), original)
                self.assertEqual((config.width, config.burst_count, config.confirm_button), (1920, 2, 'f'))
                self.assertEqual((config.hotkey_start, config.hotkey_pause), ('f8', 'f9'))

    def test_confirm_change_cannot_conflict_with_existing_hotkey(self):
        config = self.load('HOTKEY_PAUSE=e\n')
        with self.assertRaises(ValueError):
            config.save(confirm_button='e')
        self.assertEqual(config.confirm_button, 'f')

    def test_failed_save_preserves_active_config_and_original_file(self):
        config = self.load('BURST_COUNT=2\n')
        original = self.env_path.read_bytes()
        with patch('core.config.set_key', side_effect=OSError('disk unavailable')):
            with self.assertRaises(OSError):
                config.save(burst_count=5)
        self.assertEqual(config.burst_count, 2)
        self.assertEqual(self.env_path.read_bytes(), original)

    def test_save_normalizes_values_and_preserves_comments(self):
        config = self.load('# user settings\nOTHER_VALUE=keep\n')
        config.save(confirm_button=' E ', burst_count=1, hotkey_start='#')
        values = dotenv_values(self.env_path)
        self.assertEqual(config.confirm_button, 'e')
        self.assertEqual(values['CONFIRM_BUTTON'], 'e')
        self.assertEqual(values['HOTKEY_START'], '#')
        self.assertEqual(values['OTHER_VALUE'], 'keep')
        self.assertIn('# user settings', self.env_path.read_text(encoding='utf-8'))

    def test_relative_config_path_remains_bound_after_working_directory_changes(self):
        original_dir = Path.cwd()

        def safe_set_key(path, *args, **kwargs):
            if Path(path).resolve().parent != Path(self.temp.name).resolve():
                raise AssertionError('Config save escaped its temporary directory')
            return set_key(path, *args, **kwargs)

        try:
            os.chdir(self.temp.name)
            config = Config('.env')
            os.chdir(original_dir)
            with patch('core.config.set_key', side_effect=safe_set_key):
                config.save(burst_count=5)
            self.assertEqual(dotenv_values(self.env_path)['BURST_COUNT'], '5')
        finally:
            os.chdir(original_dir)

    def test_overlapping_saves_preserve_both_changes(self):
        config = self.load()
        ready = threading.Barrier(3)

        def save(**changes):
            ready.wait(timeout=3)
            config.save(**changes)

        with ThreadPoolExecutor(max_workers=2) as executor:
            first = executor.submit(save, width=2400)
            second = executor.submit(save, burst_count=5)
            ready.wait(timeout=3)
            first.result(timeout=3)
            second.result(timeout=3)
        saved = dotenv_values(self.env_path)
        self.assertEqual((saved['WIDTH'], saved['BURST_COUNT']), ('2400', '5'))
        self.assertEqual((config.width, config.burst_count), (2400, 5))


if __name__ == '__main__':
    unittest.main()
