import ctypes
from ctypes import wintypes
import os
import threading
from random import randint, uniform
from time import perf_counter, sleep
from typing import Any, Callable, Optional, Tuple, Union

import win32api
import win32gui
import win32process
from pyautogui import pixel  # type: ignore[import-untyped]
import pyautogui  # type: ignore[import-untyped]
from pynput.keyboard import Key, KeyCode, Listener as KeyListener  # type: ignore[import-untyped]
from pynput.mouse import Button, Listener as MouseListener  # type: ignore[import-untyped]

from core.config import CONFIRM_KEYS, Config

# Thiết lập DPI awareness
try:
    ctypes.windll.shcore.SetProcessDpiAwareness(2)
except Exception:
    try:
        ctypes.windll.user32.SetProcessDPIAware()
    except Exception:
        pass

# Tối ưu triệt để PyAutoGUI để không có độ trễ nền
pyautogui.PAUSE = 0.0
pyautogui.FAILSAFE = False

user32 = ctypes.windll.user32
kernel32 = ctypes.WinDLL('kernel32', use_last_error=True)
kernel32.QueryFullProcessImageNameW.argtypes = [
    wintypes.HANDLE, wintypes.DWORD, wintypes.LPWSTR, ctypes.POINTER(wintypes.DWORD),
]
kernel32.QueryFullProcessImageNameW.restype = wintypes.BOOL

# ========================== DIRECTINPUT / WIN32 KEY & MOUSE ==========================
# Bảng ánh xạ phím thông dụng sang Virtual Key code
VK_MAP = {
    "f": 0x46,
    "e": 0x45,
    "space": 0x20,
    "enter": 0x0D,
    "q": 0x51,
    "r": 0x52,
    "t": 0x54,
    "x": 0x58,
    "c": 0x43,
    "v": 0x56,
    "1": 0x31,
    "2": 0x32,
    "3": 0x33,
    "4": 0x34,
}

KEYEVENTF_KEYDOWN = 0x0000
KEYEVENTF_KEYUP = 0x0002
MOUSEEVENTF_LEFTDOWN = 0x0002
MOUSEEVENTF_LEFTUP = 0x0004


def fast_key_press(key_char: str, hold_sec: float = 0.005) -> None:
    """Gửi một lần nhấn phím qua Win32 và luôn nhả phím."""
    k = key_char.strip().lower()
    if k not in CONFIRM_KEYS:
        raise ValueError(f'Phím tương tác không được hỗ trợ: {key_char}')
    vk = VK_MAP[k] if k in VK_MAP else ord(k.upper())

    scan = user32.MapVirtualKeyW(vk, 0)
    user32.keybd_event(vk, scan, KEYEVENTF_KEYDOWN, 0)
    try:
        if hold_sec > 0:
            sleep(hold_sec)
    finally:
        user32.keybd_event(vk, scan, KEYEVENTF_KEYUP, 0)


def fast_mouse_click(hold_sec: float = 0.004) -> None:
    """Gửi tín hiệu click chuột trái trực tiếp qua Win32 API."""
    user32.mouse_event(MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
    try:
        if hold_sec > 0:
            sleep(hold_sec)
    finally:
        user32.mouse_event(MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)


def parse_key_event(key: Union[Key, KeyCode, None]) -> str:
    """Chuyển đổi đối tượng phím từ pynput thành chuỗi chuẩn hóa dễ lưu trữ."""
    if key is None:
        return ""
    if isinstance(key, Key):
        return key.name.lower()
    if isinstance(key, KeyCode):
        if key.char and key.char.isprintable():
            return key.char.lower()
        if key.vk is not None:
            # F1 - F24
            if 0x70 <= key.vk <= 0x87:
                return f"f{key.vk - 0x70 + 1}"
            # Numpad 0-9
            if 0x60 <= key.vk <= 0x69:
                return f"num_{key.vk - 0x60}"
            if key.vk == 0x6A: return "num_mult"
            if key.vk == 0x6B: return "num_add"
            if key.vk == 0x6D: return "num_sub"
            if key.vk == 0x6E: return "num_dec"
            if key.vk == 0x6F: return "num_div"
            return f"vk_{key.vk}"
    s = str(key).lower()
    if s.startswith("key."):
        return s[4:]
    return s.strip("'")


def parse_mouse_event(button: Any) -> Optional[str]:
    """Chuyển đổi nút chuột từ pynput thành chuỗi chuẩn hóa (hỗ trợ nút hông Mouse 4, Mouse 5, Mouse 3)."""
    if button is None:
        return None
    try:
        if button == Button.x1:
            return "mouse4"
        elif button == Button.x2:
            return "mouse5"
        elif button == Button.middle:
            return "mouse3"
    except Exception:
        pass
    s = str(button).lower()
    if "x1" in s:
        return "mouse4"
    elif "x2" in s:
        return "mouse5"
    elif "middle" in s:
        return "mouse3"
    return None


def format_key_display(key_str: str) -> str:
    """Định dạng chuỗi phím hiển thị đẹp trên giao diện."""
    if not key_str:
        return "Chưa đặt"
    k = key_str.lower().strip()
    display_map = {
        "mouse4": "Mouse 4",
        "mouse5": "Mouse 5",
        "mouse3": "Mouse 3",
        "space": "Space",
        "enter": "Enter",
        "return": "Enter",
        "esc": "Esc",
        "tab": "Tab",
        "backspace": "Backspace",
        "delete": "Delete",
        "insert": "Insert",
        "home": "Home",
        "end": "End",
        "page_up": "PageUp",
        "page_down": "PageDown",
        "caps_lock": "CapsLock",
        "shift": "Shift",
        "ctrl_l": "Ctrl",
        "ctrl_r": "Ctrl",
        "alt_l": "Alt",
        "alt_r": "Alt",
        "alt_gr": "AltGr",
        "num_mult": "Num *",
        "num_add": "Num +",
        "num_sub": "Num -",
        "num_dec": "Num .",
        "num_div": "Num /",
    }
    if k in display_map:
        return display_map[k]
    if k.startswith("f") and k[1:].isdigit():
        return k.upper()
    if k.startswith("num_"):
        return f"Num {k[4:]}"
    if k.startswith("vk_"):
        return f"Key({k[3:]})"
    return k.upper()


def is_admin() -> bool:
    """Kiểm tra quyền Administrator của tiến trình."""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin() != 0
    except Exception:
        return False


def get_process_executable(pid: int) -> str:
    """Đọc tên executable bằng quyền truy vấn tiến trình tối thiểu."""
    process = win32api.OpenProcess(0x1000, False, pid)  # PROCESS_QUERY_LIMITED_INFORMATION
    try:
        buffer = ctypes.create_unicode_buffer(32768)
        size = wintypes.DWORD(len(buffer))
        if not kernel32.QueryFullProcessImageNameW(int(process), 0, buffer, ctypes.byref(size)):
            raise ctypes.WinError(ctypes.get_last_error())
        return os.path.basename(buffer.value)
    finally:
        process.Close()


def is_real_genshin_window(hwnd: int) -> bool:
    """Chỉ nhận cửa sổ thuộc executable game; từ chối khi không xác minh được."""
    try:
        if not hwnd or not win32gui.IsWindow(hwnd) or not win32gui.IsWindowVisible(hwnd):
            return False
        _, pid = win32process.GetWindowThreadProcessId(hwnd)
        if pid == os.getpid():
            return False
        return get_process_executable(pid).casefold() in {'genshinimpact.exe', 'yuanshen.exe'}
    except Exception:
        return False


def get_genshin_window_info() -> Tuple[bool, Optional[int], str, int, int, int, int, bool]:
    """
    Tìm và phân tích cửa sổ Genshin Impact.
    Trả về:
    (is_foreground, hwnd, title, client_x, client_y, client_w, client_h, is_windowed)
    """
    fg_hwnd = None
    try:
        fg_hwnd = win32gui.GetForegroundWindow()
    except Exception:
        pass

    target_hwnd = None
    target_title = ""

    # 1. Kiểm tra nếu cửa sổ foreground chính là Genshin Impact thật
    if fg_hwnd and is_real_genshin_window(fg_hwnd):
        target_hwnd = fg_hwnd
        target_title = win32gui.GetWindowText(fg_hwnd).strip()

    # 2. Nếu foreground không phải Genshin, tìm cửa sổ Genshin chạy ngầm
    if not target_hwnd:
        for cls_name, win_name in [("UnityWndClass", "Genshin Impact"), ("UnityWndClass", "原神"), (None, "Genshin Impact"), (None, "原神")]:
            try:
                h = win32gui.FindWindow(cls_name, win_name)
                if h and is_real_genshin_window(h):
                    target_hwnd = h
                    target_title = win32gui.GetWindowText(h).strip()
                    break
            except Exception:
                pass

    if not target_hwnd:
        return False, None, "", 0, 0, 0, 0, False

    try:
        client_x, client_y = win32gui.ClientToScreen(target_hwnd, (0, 0))
        rect = win32gui.GetClientRect(target_hwnd)
        client_w = rect[2] - rect[0]
        client_h = rect[3] - rect[1]

        # Kiểm tra xem có phải cửa sổ (Windowed) hay toàn màn hình
        is_windowed = bool(client_x != 0 or client_y != 0)
        is_fg = bool(target_hwnd == fg_hwnd)

        return is_fg, target_hwnd, target_title, client_x, client_y, client_w, client_h, is_windowed
    except Exception:
        return False, target_hwnd, target_title, 0, 0, 0, 0, False


class AutoSkipEngine:
    """Engine xử lý tự động nhận diện và tua hội thoại Genshin Impact đa chế độ & tốc độ cao."""

    def __init__(self, config: Config):
        self.config = config
        self.status: str = "paused"  # "running", "paused", "stopped"
        self._stop_event = threading.Event()
        self._worker_thread: Optional[threading.Thread] = None
        self._listener: Optional[KeyListener] = None
        self._mouse_listener: Optional[MouseListener] = None

        # Thống kê
        self.total_skips: int = 0
        self.total_choices: int = 0
        self.current_cps: float = 0.0  # Clicks / Spam per second

        # Đo tốc độ thực tế
        self._recent_clicks = 0
        self._last_cps_time = perf_counter()

        # Cửa sổ hiện tại
        self.current_window_info = {
            "is_active": False,
            "title": "",
            "width": config.width,
            "height": config.height,
            "is_windowed": False,
            "offset_x": 0,
            "offset_y": 0,
        }

        # Callbacks
        self.on_status_change: Optional[Callable[[str], None]] = None
        self.on_log: Optional[Callable[[str, str], None]] = None  # (msg, category)
        self.on_stats_update: Optional[Callable[[int, int, float], None]] = None  # (skips, choices, cps)
        self.on_window_check: Optional[Callable[[bool, str, int, int, bool, int, int], None]] = None
        self.on_hotkey_recorded: Optional[Callable[[str, str], None]] = None  # (target, key_name)

        # Chế độ ghi nhận phím tắt tùy chỉnh (None, "start", "pause")
        self.recording_hotkey_for: Optional[str] = None

        # Trạng thái log tránh spam
        self._last_log_state = ""
        self._last_log_time = 0.0

    def log(self, msg: str, category: str = "info", throttle_sec: float = 0.0) -> None:
        """Ghi log có hỗ trợ throttle tránh spam liên tục cùng một trạng thái."""
        now = perf_counter()
        if throttle_sec > 0:
            if msg == self._last_log_state and (now - self._last_log_time) < throttle_sec:
                return
            self._last_log_state = msg
            self._last_log_time = now

        if self.on_log:
            self.on_log(msg, category)
        else:
            print(f"[{category.upper()}] {msg}")

    # ========================== TÍNH TOÁN TỌA ĐỘ THEO TỶ LỆ ==========================
    def calculate_relative_coords(self, w: int, h: int) -> dict:
        """
        Tính toán tọa độ các điểm ảnh mục tiêu dựa trên kích thước vùng render game (w, h).
        Hỗ trợ 16:9, 16:10, 4:3, 5:4, UltraWide 21:9.
        """
        if w <= 0 or h <= 0:
            w, h = 1920, 1080

        ratio = float(w) / float(h)
        coords = {}

        # 1. ICON PHÁT TỰ ĐỘNG (PLAYING_ICON - neo ở góc trên bên trái)
        if ratio > 1.85:  # Ultrawide
            coords["play_x"] = min(int(84 + (w - 1920) * ((230 - 84) / 1920)), 230)
            coords["play_y"] = int(46.0 / 1080.0 * h)
        else:
            coords["play_x"] = int(84.0 / 1920.0 * w)
            coords["play_y"] = int(46.0 / 1080.0 * h)

        # 2. BIỂU TƯỢNG HỘI THOẠI & LỰA CHỌN (DIALOGUE_ICON)
        if 1.70 <= ratio <= 1.85:
            # Tỷ lệ 16:9 (1920x1080, 1366x768, 1280x720, 1176x664, 2K, 4K)
            coords["diag_x"] = int(1301.0 / 1920.0 * w)
            coords["diag_lower_y"] = int(808.0 / 1080.0 * h)
            coords["diag_higher_y"] = int(790.0 / 1080.0 * h)
        elif 1.50 <= ratio < 1.70:
            # Tỷ lệ 16:10 (1680x1050, 1440x900, 1280x800, 2880x1800, 2560x1600)
            coords["diag_x"] = int(1301.0 / 1920.0 * w)
            coords["diag_lower_y"] = int(h * 0.761)
            coords["diag_higher_y"] = int(h * 0.700)
        elif ratio < 1.50:
            # Tỷ lệ 4:3 / 5:4 (1440x1080, 1280x1024)
            coords["diag_x"] = int(1301.0 / 1920.0 * w)
            coords["diag_lower_y"] = int(h * 0.760)
            coords["diag_higher_y"] = int(h * 0.700)
        else:
            # Ultrawide 21:9
            coords["diag_x"] = int(1301 + (w - 1920) * ((2770 - 1301) / 1920 + 0.02))
            coords["diag_lower_y"] = int(810.0 / 1080.0 * h)
            coords["diag_higher_y"] = int(792.0 / 1080.0 * h)

        # 3. MÀN HÌNH TẢI (LOADING_SCREEN)
        coords["load_x"] = int(1200.0 / 1920.0 * w)
        coords["load_y"] = int(700.0 / 1080.0 * h)

        return coords

    @staticmethod
    def is_color_close(c1, c2, tol: int = 28) -> bool:
        if not c1 or not c2:
            return False
        return (
            abs(c1[0] - c2[0]) <= tol and
            abs(c1[1] - c2[1]) <= tol and
            abs(c1[2] - c2[2]) <= tol
        )

    @staticmethod
    def is_white_like(c, threshold: int = 220) -> bool:
        if not c:
            return False
        return c[0] >= threshold and c[1] >= threshold and c[2] >= threshold

    @staticmethod
    def is_golden_amber(c) -> bool:
        """Kiểm tra màu vàng hổ phách/vàng kim đặc trưng của Genshin (Nhấn để tiếp tục / Biểu tượng thoi)."""
        if not c:
            return False
        r, g, b = c
        return r >= 170 and g >= 115 and b <= 65 and r > g

    # ========================== NHẬN DIỆN TRẠNG THÁI ==========================
    def is_narrative_screen(self, off_x: int, off_y: int, cur_w: int, cur_h: int) -> bool:
        """
        Kiểm tra màn hình dẫn chuyện chữ trắng nền đen/tối ('Nhấn để tiếp tục' kèm biểu tượng thoi vàng).
        Thường xuất hiện trong cốt truyện ma thần, truyền thuyết, sự kiện (Cutscene monologue / Black narrative).
        """
        if cur_w <= 0 or cur_h <= 0:
            return False

        try:
            # 1. Kiểm tra nhanh nền đen/tối ở 2 bên góc dưới để bỏ qua ngay nếu đang trong game sáng
            y_test = off_y + int(0.94 * cur_h)
            bg_l = pixel(off_x + int(0.20 * cur_w), y_test)
            bg_r = pixel(off_x + int(0.80 * cur_w), y_test)
            if not (bg_l[0] < 55 and bg_l[1] < 55 and bg_l[2] < 55 and
                    bg_r[0] < 55 and bg_r[1] < 55 and bg_r[2] < 55):
                return False

            # 2. Quét biểu tượng thoi vàng (diamond) hoặc dòng chữ vàng 'Nhấn để tiếp tục' ở giữa đáy màn hình
            cx = off_x + cur_w // 2

            # Quét dải icon thoi vàng (~0.935h đến ~0.960h)
            for y_rel in [0.947, 0.942, 0.952, 0.937, 0.957]:
                target_y = off_y + int(y_rel * cur_h)
                for dx in [0, -3, 3, -6, 6]:
                    px = pixel(cx + dx, target_y)
                    if self.is_golden_amber(px):
                        return True

            # Quét dải chữ 'Nhấn để tiếp tục' (~0.885h đến ~0.915h)
            for y_rel in [0.895, 0.902, 0.908, 0.888]:
                target_y = off_y + int(y_rel * cur_h)
                for dx in range(-40, 41, 10):
                    px = pixel(cx + dx, target_y)
                    if self.is_golden_amber(px):
                        return True

        except Exception:
            pass
        return False

    def is_dialogue_playing(self, screen_play_x: int, screen_play_y: int, cur_w: int = 1920, cur_h: int = 1080) -> bool:
        """Kiểm tra nút Auto Play với dải dung sai lân cận và chống nhận diện nhầm với cát/tuyết/minimap."""
        found = False
        try:
            px = pixel(screen_play_x, screen_play_y)
            if self.is_color_close(px, (236, 229, 216), tol=25):
                found = True
        except Exception:
            pass

        if not found:
            # Quét dải xung quanh nếu tâm chưa khớp
            offsets = [(-3, 0), (3, 0), (0, -3), (0, 3), (-2, -2), (2, 2)]
            for dx, dy in offsets:
                try:
                    px = pixel(screen_play_x + dx, screen_play_y + dy)
                    if self.is_color_close(px, (236, 229, 216), tol=25):
                        found = True
                        break
                except Exception:
                    pass

        if not found:
            return False

        # Chống nhận diện nhầm với mảng cát/tuyết hoặc minimap:
        # Icon Auto-Play là biểu tượng nhỏ (▶▶), xung quanh nó cách 25-35px KHÔNG thể cùng màu (236, 229, 216)
        try:
            dx_chk = int(28.0 / 1920.0 * cur_w)
            dy_chk = int(28.0 / 1080.0 * cur_h)
            px_l = pixel(screen_play_x - dx_chk, screen_play_y)
            px_r = pixel(screen_play_x + dx_chk, screen_play_y)
            px_u = pixel(screen_play_x, screen_play_y - dy_chk)
            # Nếu cả 3 điểm xung quanh cũng đều khớp màu (236, 229, 216) -> Đó là mảng cát sa mạc/tuyết
            if (self.is_color_close(px_l, (236, 229, 216), tol=25) and
                self.is_color_close(px_r, (236, 229, 216), tol=25) and
                self.is_color_close(px_u, (236, 229, 216), tol=25)):
                return False
        except Exception:
            pass

        return True

    def is_dialogue_option_available(
        self,
        screen_load_x: int,
        screen_load_y: int,
        screen_diag_x: int,
        screen_lower_y: int,
        screen_higher_y: int,
        cur_w: int = 1920,
        cur_h: int = 1080,
    ) -> Optional[Tuple[int, int]]:
        """Trả về vị trí click của đáp án thấp nhất nhận diện được, hoặc None."""
        # 1. Kiểm tra màn hình tải trắng
        try:
            load_px = pixel(screen_load_x, screen_load_y)
            if self.is_white_like(load_px, threshold=250):
                return None
        except Exception:
            return None

        # 2. Quét nhanh vị trí biểu tượng đối thoại
        mid_y = (screen_lower_y + screen_higher_y) // 2
        for target_y in sorted({screen_lower_y, screen_higher_y, mid_y}, reverse=True):
            try:
                px = pixel(screen_diag_x, target_y)
                if self.is_white_like(px, threshold=210) or self.is_color_close(px, (236, 229, 216), tol=30):
                    # Đã thấy điểm sáng nghi vấn biểu tượng hội thoại -> Kiểm tra ngữ cảnh để chống nhận diện nhầm:
                    # Nếu xung quanh điểm này (trên, dưới, trái) đều là màu trắng sáng thì đó là mây/tuyết/bầu trời/tường trắng
                    off_above = int(30.0 / 1080.0 * cur_h)
                    off_below = int(30.0 / 1080.0 * cur_h)
                    off_left = int(45.0 / 1920.0 * cur_w)

                    px_above = pixel(screen_diag_x, target_y - off_above)
                    px_below = pixel(screen_diag_x, target_y + off_below)
                    px_left = pixel(screen_diag_x - off_left, target_y)

                    if (self.is_white_like(px_above, 205) and
                        self.is_white_like(px_below, 205) and
                        self.is_white_like(px_left, 205)):
                        continue

                    # Kiểm tra thêm nền hộp thoại (bubble background):
                    # Nút chọn hội thoại trong game luôn có dải nền xám tối/đen mờ (dark translucent)
                    x_bubble = screen_diag_x + int(50.0 / 1920.0 * cur_w)
                    px_bubble_t = pixel(x_bubble, target_y - int(12.0 / 1080.0 * cur_h))
                    px_bubble_b = pixel(x_bubble, target_y + int(12.0 / 1080.0 * cur_h))

                    # Nếu cả 2 điểm trên dưới trong nút đều trắng tinh -> không phải nút có nền tối
                    if self.is_white_like(px_bubble_t, 215) and self.is_white_like(px_bubble_b, 215):
                        continue

                    return x_bubble, target_y
            except Exception:
                pass

        return None

    def is_loading_screen(self, screen_load_x: int, screen_load_y: int) -> bool:
        """Kiểm tra xem có phải màn hình tải trắng của game không."""
        try:
            load_px = pixel(screen_load_x, screen_load_y)
            return self.is_white_like(load_px, threshold=250)
        except Exception:
            return False

    # ========================== THAO TÁC PHÍM & SPAM ==========================
    def _can_send_input(self, hwnd: Optional[int]) -> bool:
        if not hwnd or self.status != 'running' or self._stop_event.is_set() or self.recording_hotkey_for:
            return False
        try:
            return win32gui.GetForegroundWindow() == hwnd
        except Exception:
            return False

    def _execute_spam_burst(
        self, key_char: str, burst_count: int, hold_sec: float, with_click: bool,
        hwnd: Optional[int], click_position: Optional[Tuple[int, int]] = None,
    ) -> int:
        """Kiểm tra lại quyền gửi trước từng thao tác; đáp án chỉ click một lần."""
        if click_position is not None:
            if not self._can_send_input(hwnd):
                return 0
            pyautogui.moveTo(*click_position, duration=0)
            if not self._can_send_input(hwnd):
                return 0
            fast_mouse_click(hold_sec=hold_sec)
            return 1

        executed = 0
        for _ in range(burst_count):
            if not self._can_send_input(hwnd):
                break
            fast_key_press(key_char, hold_sec=hold_sec)
            executed += 1
            if with_click:
                if not self._can_send_input(hwnd):
                    break
                fast_mouse_click(hold_sec=hold_sec)
        return executed

    def _get_mode_params(self) -> Tuple[float, int, float, bool]:
        """
        Lấy thông số theo chế độ tốc độ đã cấu hình:
        Trả về: (interval_sec, burst_count, hold_sec, allow_break)
        """
        mode = self.config.spam_mode.lower()
        cfg_burst = max(1, min(5, self.config.burst_count))

        if mode == "safe":
            # Mô phỏng người thật: chậm, ngẫu nhiên, có nghỉ ngơi
            interval = uniform(0.15, 0.22) if randint(1, 6) == 6 else uniform(0.12, 0.18)
            return interval, 1, 0.015, True

        elif mode == "fast":
            # Chế độ Nhanh: ~15-20 lần/giây, không nghỉ ngơi
            interval = 0.05
            burst = max(1, cfg_burst if cfg_burst <= 2 else 2)
            return interval, burst, 0.005, False

        elif mode == "extreme":
            # Chế độ Điên cuồng: ~80-100+ lần/giây, tốc độ tối đa
            interval = 0.008
            burst = cfg_burst
            return interval, burst, 0.002, False

        else:  # "turbo" (Mặc định)
            # Chế độ Siêu tốc: ~40-60 lần/giây, tua thoại xé gió
            interval = 0.02
            burst = max(1, cfg_burst)
            return interval, burst, 0.004, False

    def _should_take_break(self) -> bool:
        if self.config.spam_mode != "safe":
            return False
        return randint(1, 25) == 1

    # ========================== VÒNG LẶP CHÍNH ==========================
    def _loop(self) -> None:
        last_press = 0.0
        last_break_check = perf_counter()
        break_check_interval = 30.0
        last_game_active: Optional[bool] = None

        self._last_cps_time = perf_counter()
        self._recent_clicks = 0

        while not self._stop_event.is_set():
            now = perf_counter()

            # Cập nhật CPS (Clicks Per Second) mỗi 0.5s
            cps_elapsed = now - self._last_cps_time
            if cps_elapsed >= 0.5:
                self.current_cps = round(self._recent_clicks / cps_elapsed, 1)
                self._recent_clicks = 0
                self._last_cps_time = now
                if self.on_stats_update:
                    self.on_stats_update(self.total_skips, self.total_choices, self.current_cps)

            # Nếu đang pause
            if self.status != "running":
                sleep(0.15)
                last_press = perf_counter()
                continue

            # 1. Quét thông tin cửa sổ Genshin Impact
            is_fg, hwnd, title, client_x, client_y, client_w, client_h, is_windowed = get_genshin_window_info()

            # Xác định kích thước và vị trí vùng render game
            if hwnd and self.config.auto_window_mode and client_w > 100 and client_h > 100:
                cur_w, cur_h = client_w, client_h
                off_x, off_y = client_x, client_y
            else:
                cur_w, cur_h = self.config.width, self.config.height
                off_x, off_y = (client_x, client_y) if hwnd else (0, 0)

            # Cập nhật thông tin cửa sổ hiện tại
            self.current_window_info.update({
                "is_active": is_fg,
                "title": title,
                "width": cur_w,
                "height": cur_h,
                "is_windowed": is_windowed,
                "offset_x": off_x,
                "offset_y": off_y,
            })

            # Thông báo cho UI
            if self.on_window_check:
                self.on_window_check(is_fg, title, cur_w, cur_h, is_windowed, off_x, off_y)

            # Ghi log khi đổi trạng thái cửa sổ game
            if is_fg != last_game_active:
                last_game_active = is_fg
                if is_fg:
                    mode_str = "Cửa Sổ" if is_windowed else "Toàn Màn Hình"
                    pos_str = f" tại ({off_x}, {off_y})" if is_windowed else ""
                    self.log(f"Đã nhận diện Genshin: {cur_w}x{cur_h} [{mode_str}]{pos_str}", "success")
                else:
                    self.log("Đang chờ chuyển sang cửa sổ Genshin Impact...", "info")

            if not is_fg:
                sleep(0.3)
                continue

            # 2. Tính toán tọa độ tuyệt đối trên màn hình
            rel_coords = self.calculate_relative_coords(cur_w, cur_h)
            screen_play_x = off_x + rel_coords["play_x"]
            screen_play_y = off_y + rel_coords["play_y"]
            screen_diag_x = off_x + rel_coords["diag_x"]
            screen_lower_y = off_y + rel_coords["diag_lower_y"]
            screen_higher_y = off_y + rel_coords["diag_higher_y"]
            screen_load_x = off_x + rel_coords["load_x"]
            screen_load_y = off_y + rel_coords["load_y"]

            # Lấy thông số tốc độ hiện tại
            interval, burst, hold_sec, allow_break = self._get_mode_params()

            # 3. Kiểm tra điều kiện kích hoạt theo chế độ
            trigger_mode = self.config.trigger_mode
            dialogue_active = False
            dialogue_playing = False
            is_choice = False
            choice_position = None

            # Kiểm tra màn hình dẫn chuyện chữ trắng nền đen ('Nhấn để tiếp tục')
            is_narrative = self.is_narrative_screen(off_x, off_y, cur_w, cur_h)

            if is_narrative:
                dialogue_active = True
            elif trigger_mode == "always":
                # Chế độ Luôn Spam trong Game (Loot & Skip):
                # Bỏ qua nếu đang ở màn hình tải trắng
                if self.is_loading_screen(screen_load_x, screen_load_y):
                    sleep(0.1)
                    continue

                # Kiểm tra xem có hội thoại hoặc lựa chọn đáp án không
                dialogue_playing = self.is_dialogue_playing(screen_play_x, screen_play_y, cur_w, cur_h)
                choice_position = self.is_dialogue_option_available(
                    screen_load_x, screen_load_y, screen_diag_x, screen_lower_y, screen_higher_y, cur_w, cur_h
                )
                is_choice = choice_position is not None
                dialogue_active = True
            else:
                # Chế độ Tự Động Nhận Diện Thoại:
                dialogue_playing = self.is_dialogue_playing(screen_play_x, screen_play_y, cur_w, cur_h)
                choice_position = self.is_dialogue_option_available(
                    screen_load_x, screen_load_y, screen_diag_x, screen_lower_y, screen_higher_y, cur_w, cur_h
                )
                is_choice = choice_position is not None
                dialogue_active = dialogue_playing or is_choice

            if not dialogue_active:
                sleep(0.04)
                continue

            # 4. Mô phỏng nghỉ ngơi ngẫu nhiên (chỉ ở chế độ Safe)
            if allow_break and (now - last_break_check > break_check_interval):
                last_break_check = now
                if self._should_take_break():
                    break_sec = uniform(3.0, 5.0)
                    self.log(f"Tạm nghỉ {break_sec:.1f}s mô phỏng người thật...", "break")
                    self._stop_event.wait(break_sec)
                    last_press = perf_counter()
                    continue

            # 5. Thực hiện spam phím tương tác
            if is_narrative:
                # Màn hình dẫn chuyện: Cần Click chuột trái hoặc Space để chuyển câu (giữ nhịp êm ái ~0.15s)
                narrative_interval = max(0.15, interval)
                if now - last_press >= narrative_interval:
                    executed = self._execute_spam_burst('space', 1, hold_sec, True, hwnd)
                    self.total_skips += executed
                    self._recent_clicks += executed
                    if executed:
                        self.log("Đang tự động bấm qua màn hình dẫn chuyện ('Nhấn để tiếp tục')...", "skip", throttle_sec=3.0)
                    last_press = perf_counter()
            elif now - last_press >= interval:
                confirm_key = self.config.confirm_button.lower()

                # QUAN TRỌNG VỀ CLICK CHUỘT TRÁI (CHỐNG SPAM ĐÁNH THƯỜNG):
                # 1. Trong chế độ 'always' (chạy map nhặt đồ):
                #    CHỈ click chuột trái khi THẬT SỰ có bảng chọn đáp án (is_choice)
                #    hoặc khi đang có hội thoại (dialogue_playing) VÀ người dùng bật click_combo.
                #    Khi chỉ đang chạy nhặt rác ngoài map -> Tuyệt đối KHÔNG click chuột trái (with_click = False).
                # 2. Trong chế độ 'dialogue':
                #    Click chuột trái khi có bảng chọn (is_choice) hoặc khi người dùng bật click_combo.
                if trigger_mode == "always":
                    with_click = is_choice or (dialogue_playing and self.config.click_combo)
                else:
                    with_click = is_choice or self.config.click_combo

                executed_count = self._execute_spam_burst(
                    confirm_key,
                    burst_count=burst,
                    hold_sec=hold_sec,
                    with_click=with_click,
                    hwnd=hwnd,
                    click_position=choice_position,
                )

                if is_choice:
                    self.total_choices += executed_count
                else:
                    self.total_skips += executed_count

                self._recent_clicks += executed_count
                last_press = perf_counter()

            # Giãn cách vòng lặp siêu ngắn để giảm tải CPU
            sleep(0.002)

    # ========================== ĐIỀU KHIỂN & PHÍM TẮT ==========================
    def start(self) -> None:
        """Kích hoạt chạy Auto-Skip."""
        if self._stop_event.is_set():
            return
        self.status = "running"
        if self.on_status_change:
            self.on_status_change("running")
        mode_text = {
            "safe": "An toàn (Safe)",
            "fast": "Nhanh (Fast)",
            "turbo": "Siêu tốc (Turbo)",
            "extreme": "Điên cuồng (Extreme)"
        }.get(self.config.spam_mode, self.config.spam_mode)
        trigger_text = "Luôn spam" if self.config.trigger_mode == "always" else "Khi có thoại"
        self.log(f"BẮT ĐẦU: Chế độ [{mode_text}] | Kích hoạt: [{trigger_text}]", "success")

    def pause(self) -> None:
        """Tạm dừng Auto-Skip."""
        self.status = "paused"
        self.current_cps = 0.0
        if self.on_status_change:
            self.on_status_change("paused")
        if self.on_stats_update:
            self.on_stats_update(self.total_skips, self.total_choices, 0.0)
        start_disp = format_key_display(self.config.hotkey_start)
        self.log(f"TẠM DỪNG (Bấm [{start_disp}] để tiếp tục)", "info")

    def toggle(self) -> None:
        """Chuyển đổi giữa chạy và tạm dừng."""
        if self.status == "running":
            self.pause()
        else:
            self.start()

    def reset_stats(self) -> None:
        self.total_skips = 0
        self.total_choices = 0
        self.current_cps = 0.0
        self._recent_clicks = 0
        if self.on_stats_update:
            self.on_stats_update(0, 0, 0.0)

    def _on_key_press(self, key: Union[Key, KeyCode, None]) -> None:
        key_name = parse_key_event(key)
        if not key_name:
            return

        if key_name == 'f12':
            self.stop()
            return

        # 1. Nếu đang ở chế độ gán phím tắt mới
        if self.recording_hotkey_for:
            self._finish_hotkey_recording(key_name)
            return

        # 2. Xử lý phím tắt hoạt động thông thường
        start_key = self.config.hotkey_start.lower()
        pause_key = self.config.hotkey_pause.lower()

        if key_name == start_key:
            self.start()
        elif key_name == pause_key:
            self.pause()

    def _finish_hotkey_recording(self, key_name: str) -> None:
        target = self.recording_hotkey_for
        self.recording_hotkey_for = None
        result = 'cancelled' if key_name == 'esc' else key_name
        if key_name != 'esc':
            try:
                self.config.save(**{f'hotkey_{target}': key_name})
            except (ValueError, OSError) as exc:
                result = f'error:{exc}'
        if self.on_hotkey_recorded:
            self.on_hotkey_recorded(target, result)

    def _on_mouse_click(self, x: int, y: int, button: Any, pressed: bool) -> None:
        if not pressed:
            return

        mouse_name = parse_mouse_event(button)
        if not mouse_name:
            return

        # 1. Nếu đang ở chế độ gán phím tắt mới (hỗ trợ Mouse 4, Mouse 5, Mouse 3)
        if self.recording_hotkey_for:
            self._finish_hotkey_recording(mouse_name)
            return

        # 2. Xử lý kích hoạt / tạm dừng bình thường qua nút chuột
        start_key = self.config.hotkey_start.lower()
        pause_key = self.config.hotkey_pause.lower()

        if mouse_name == start_key:
            self.start()
        elif mouse_name == pause_key:
            self.pause()

    def run_in_background(self) -> None:
        """Khởi động worker thread, keyboard listener và mouse listener toàn cục."""
        if self._worker_thread and self._worker_thread.is_alive():
            return
        self._stop_event.clear()
        self._worker_thread = threading.Thread(target=self._loop, daemon=True)
        self._worker_thread.start()

        try:
            self._listener = KeyListener(
                on_press=self._on_key_press,
                win32_event_filter=lambda msg, data: not (data.flags & 0x10),  # LLKHF_INJECTED
            )
            self._listener.start()
        except Exception as e:
            self.log(f"Không thể kích hoạt hook bàn phím toàn cục: {e}", "warning")

        try:
            self._mouse_listener = MouseListener(on_click=self._on_mouse_click)
            self._mouse_listener.start()
        except Exception as e:
            self.log(f"Không thể kích hoạt hook chuột toàn cục: {e}", "warning")

    def stop(self) -> None:
        """Dừng hoàn toàn engine."""
        if self._stop_event.is_set():
            return
        self.status = "stopped"
        self._stop_event.set()
        if self._listener:
            try:
                self._listener.stop()
            except Exception:
                pass
        if self._mouse_listener:
            try:
                self._mouse_listener.stop()
            except Exception:
                pass
        if self._worker_thread and self._worker_thread is not threading.current_thread():
            self._worker_thread.join(timeout=1.0)
        if self.on_status_change:
            self.on_status_change("stopped")
        self.log("ĐÃ DỪNG chương trình.", "info")
