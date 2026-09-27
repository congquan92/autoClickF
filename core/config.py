import os
import ctypes
from typing import Tuple, Dict, Any
from dotenv import find_dotenv, load_dotenv, set_key

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
        self.env_path = env_path
        self.load()

    def load(self) -> None:
        load_dotenv(self.env_path, override=True)
        detected_w, detected_h = get_screen_resolution()

        w_env = os.getenv("WIDTH")
        h_env = os.getenv("HEIGHT")

        self.width: int = int(w_env) if w_env and w_env.isdigit() else detected_w
        self.height: int = int(h_env) if h_env and h_env.isdigit() else detected_h
        self.confirm_button: str = os.getenv("CONFIRM_BUTTON", "f").lower()
        self.device: str = os.getenv("DEVICE", "mnk")
        self.always_on_top: bool = os.getenv("ALWAYS_ON_TOP", "true").lower() in ("true", "1", "yes")
        self.human_simulation: bool = os.getenv("HUMAN_SIMULATION", "true").lower() in ("true", "1", "yes")
        self.auto_window_mode: bool = os.getenv("AUTO_WINDOW_MODE", "true").lower() in ("true", "1", "yes")
        self.resolution_preset: str = os.getenv("RESOLUTION_PRESET", "auto")

        # Khởi tạo file .env nếu chưa có
        if not os.path.exists(self.env_path):
            self.save(
                width=self.width,
                height=self.height,
                confirm_button=self.confirm_button,
                device=self.device,
                always_on_top=self.always_on_top,
                human_simulation=self.human_simulation,
                auto_window_mode=self.auto_window_mode,
                resolution_preset=self.resolution_preset
            )

    def save(self, **kwargs: Any) -> None:
        """Lưu các thuộc tính vào file .env và cập nhật instance."""
        dotenv_file = find_dotenv(self.env_path) or self.env_path
        
        # Đảm bảo file tồn tại
        if not os.path.exists(dotenv_file):
            with open(dotenv_file, "w", encoding="utf-8") as f:
                f.write("")

        for key, val in kwargs.items():
            setattr(self, key.lower(), val)
            env_key = key.upper()
            val_str = str(val).lower() if isinstance(val, bool) else str(val)
            set_key(dotenv_file, env_key, val_str, quote_mode="never")
