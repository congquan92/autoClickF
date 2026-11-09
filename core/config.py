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
        self.auto_window_mode: bool = os.getenv("AUTO_WINDOW_MODE", "true").lower() in ("true", "1", "yes")
        self.resolution_preset: str = os.getenv("RESOLUTION_PRESET", "auto")

        # Phím tắt toàn cục tùy chỉnh (mặc định là F8 và F9)
        self.hotkey_start: str = os.getenv("HOTKEY_START", "f8").lower()
        self.hotkey_pause: str = os.getenv("HOTKEY_PAUSE", "f9").lower()

        # Chế độ tốc độ spam: "safe", "fast", "turbo", "extreme"
        spam_mode_env = os.getenv("SPAM_MODE")
        if spam_mode_env and spam_mode_env.lower() in ("safe", "fast", "turbo", "extreme"):
            self.spam_mode: str = spam_mode_env.lower()
        else:
            self.spam_mode = "turbo"

        # Tương thích ngược với human_simulation
        self.human_simulation: bool = (self.spam_mode == "safe")

        # Chế độ kích hoạt: "dialogue" (chỉ khi có hội thoại) | "always" (luôn spam khi ở trong game)
        trigger_mode_env = os.getenv("TRIGGER_MODE", "dialogue").lower()
        self.trigger_mode: str = trigger_mode_env if trigger_mode_env in ("dialogue", "always") else "dialogue"

        # Số lần spam phím mỗi nhịp kích hoạt (burst count)
        burst_env = os.getenv("BURST_COUNT", "2")
        self.burst_count: int = int(burst_env) if burst_env.isdigit() and int(burst_env) > 0 else 2

        # Kết hợp click chuột trái để tua và chọn đáp án siêu tốc
        self.click_combo: bool = os.getenv("CLICK_COMBO", "false").lower() in ("true", "1", "yes")

        # Khởi tạo hoặc cập nhật file .env nếu chưa có
        if not os.path.exists(self.env_path):
            self.save(
                width=self.width,
                height=self.height,
                confirm_button=self.confirm_button,
                device=self.device,
                always_on_top=self.always_on_top,
                hotkey_start=self.hotkey_start,
                hotkey_pause=self.hotkey_pause,
                spam_mode=self.spam_mode,
                trigger_mode=self.trigger_mode,
                burst_count=self.burst_count,
                click_combo=self.click_combo,
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

        # Đồng bộ human_simulation nếu spam_mode thay đổi
        if "spam_mode" in kwargs:
            self.human_simulation = (self.spam_mode == "safe")
            set_key(dotenv_file, "HUMAN_SIMULATION", str(self.human_simulation).lower(), quote_mode="never")
