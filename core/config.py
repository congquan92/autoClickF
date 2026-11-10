import os
import ctypes
from pathlib import Path
import re
import tempfile
import threading
from typing import Tuple, Any
from dotenv import dotenv_values, set_key


CONFIRM_KEYS = frozenset('abcdefghijklmnopqrstuvwxyz0123456789') | {'space', 'enter'}
HOTKEY_NAMES = {
    'esc', 'tab', 'space', 'enter', 'backspace', 'delete', 'insert', 'home', 'end',
    'page_up', 'page_down', 'up', 'down', 'left', 'right', 'caps_lock', 'num_lock',
    'scroll_lock', 'print_screen', 'pause', 'shift', 'shift_l', 'shift_r', 'ctrl',
    'ctrl_l', 'ctrl_r', 'alt', 'alt_l', 'alt_r', 'alt_gr', 'cmd', 'cmd_l', 'cmd_r',
    'menu', 'media_play_pause', 'media_volume_mute', 'media_volume_down',
    'media_volume_up', 'media_previous', 'media_next', 'mouse3', 'mouse4', 'mouse5',
    'num_mult', 'num_add', 'num_sub', 'num_dec', 'num_div',
} | {f'f{i}' for i in range(1, 25)} | {f'num_{i}' for i in range(10)}


def validate_hotkeys(start: str, pause: str, confirm: str) -> None:
    for key in (start, pause):
        valid = (len(key) == 1 and key.isprintable() and not key.isspace()) or key in HOTKEY_NAMES
        if re.fullmatch(r'vk_\d{1,3}', key):
            valid = 0 <= int(key[3:]) <= 255
        if not valid:
            raise ValueError(f'Phím tắt không được hỗ trợ: {key}')
        if key in {'f12', 'space', confirm}:
            raise ValueError(f'Không thể dùng [{key.upper()}]: phím được dành cho thao tác của tool.')
    if start == pause:
        raise ValueError('Phím Bắt đầu và Tạm dừng phải khác nhau.')

try:
    from win32api import GetSystemMetrics  # type: ignore[import-untyped]
except ImportError:
    GetSystemMetrics = None


def get_screen_resolution() -> Tuple[int, int]:
    """Lấy độ phân giải thực của màn hình chính."""
    # Đảm bảo DPI awareness trước khi đo
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(2)
    except Exception:
        try:
            ctypes.windll.user32.SetProcessDPIAware()
        except Exception:
            pass

    if GetSystemMetrics:
        try:
            w = int(GetSystemMetrics(0))
            h = int(GetSystemMetrics(1))
            if w > 0 and h > 0:
                return w, h
        except Exception:
            pass

    try:
        user32 = ctypes.windll.user32
        return int(user32.GetSystemMetrics(0)), int(user32.GetSystemMetrics(1))
    except Exception:
        return 1920, 1080


class Config:
    """Quản lý nạp và lưu cấu hình cho Auto-Skip."""

    def __init__(self, env_path: str = ".env"):
        self.env_path = str(Path(env_path).resolve())
        self._lock = threading.RLock()
        self.load()

    def load(self) -> None:
        detected_w, detected_h = get_screen_resolution()
        defaults = {
            'width': detected_w, 'height': detected_h, 'confirm_button': 'f',
            'always_on_top': True, 'auto_window_mode': True, 'resolution_preset': 'auto',
            'hotkey_start': 'f8', 'hotkey_pause': 'f9', 'spam_mode': 'turbo',
            'trigger_mode': 'dialogue', 'burst_count': 2, 'click_combo': False,
        }
        values = {**os.environ, **dotenv_values(self.env_path)}
        self.warnings = []
        for key, default in defaults.items():
            value = values.get(key.upper(), default)
            try:
                value = self._validate_value(key, value)
            except (ValueError, TypeError):
                self.warnings.append(f'{key.upper()} không hợp lệ; dùng {default}.')
                value = default
            setattr(self, key, value)
        try:
            validate_hotkeys(self.hotkey_start, self.hotkey_pause, self.confirm_button)
        except ValueError as exc:
            self.warnings.append(f'{exc} Đã khôi phục F8/F9.')
            self.hotkey_start, self.hotkey_pause = 'f8', 'f9'
        if not Path(self.env_path).exists():
            self.save(**{key: getattr(self, key) for key in defaults})

    @staticmethod
    def _validate_value(key: str, value: Any) -> Any:
        if key in {'width', 'height', 'burst_count'}:
            if isinstance(value, bool) or not re.fullmatch(r'\d+', str(value)):
                raise ValueError(f'{key.upper()} phải là số nguyên dương.')
            value = int(value)
            limit = 5 if key == 'burst_count' else 16384
            if not 1 <= value <= limit:
                raise ValueError(f'{key.upper()} phải nằm trong khoảng 1–{limit}.')
        elif key in {'always_on_top', 'auto_window_mode', 'click_combo'}:
            text = str(value).strip().lower()
            if text not in {'true', 'false', '1', '0', 'yes', 'no'}:
                raise ValueError(f'{key.upper()} phải là true hoặc false.')
            value = text in {'true', '1', 'yes'}
        elif key in {'confirm_button', 'hotkey_start', 'hotkey_pause', 'spam_mode', 'trigger_mode'}:
            value = str(value).strip().lower()
            choices = {
                'confirm_button': CONFIRM_KEYS,
                'spam_mode': {'safe', 'fast', 'turbo', 'extreme'},
                'trigger_mode': {'dialogue', 'always'},
            }
            if key in choices and value not in choices[key]:
                raise ValueError(f'{key.upper()} không được hỗ trợ: {value}')
        elif key == 'resolution_preset':
            value = str(value)
        else:
            raise ValueError(f'Thiết lập không được hỗ trợ: {key}')
        return value

    def save(self, **kwargs: Any) -> None:
        """Lưu các thuộc tính vào file .env và cập nhật instance."""
        with self._lock:
            changes = {key.lower(): self._validate_value(key.lower(), val) for key, val in kwargs.items()}
            validate_hotkeys(
                changes.get('hotkey_start', self.hotkey_start),
                changes.get('hotkey_pause', self.hotkey_pause),
                changes.get('confirm_button', self.confirm_button),
            )
            path = Path(self.env_path)
            # Hoàn tất toàn bộ bản ghi trước khi thay file và cấu hình đang chạy.
            with tempfile.NamedTemporaryFile(dir=path.parent, delete=False) as temp:
                temp_path = Path(temp.name)
            try:
                temp_path.write_bytes(path.read_bytes() if path.exists() else b'')
                for key, value in changes.items():
                    text = str(value).lower() if isinstance(value, bool) else str(value)
                    set_key(str(temp_path), key.upper(), text, quote_mode='always')
                os.replace(temp_path, path)
            finally:
                temp_path.unlink(missing_ok=True)
            self.__dict__.update(changes)
