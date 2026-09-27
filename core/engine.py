import ctypes
import os
import sys
import threading
from random import randint, uniform
from time import perf_counter, sleep
from typing import Callable, Optional, Tuple, Union

import win32gui
from pyautogui import getActiveWindowTitle, pixel  # type: ignore[import-untyped]
import pyautogui  # type: ignore[import-untyped]
from pynput.keyboard import Key, KeyCode, Listener  # type: ignore[import-untyped]

from core.config import Config

# Thiết lập DPI awareness
try:
    ctypes.windll.shcore.SetProcessDpiAwareness(2)
except Exception:
    try:
        ctypes.windll.user32.SetProcessDPIAware()
    except Exception:
        pass


def is_admin() -> bool:
    """Kiểm tra quyền Administrator của tiến trình."""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin() != 0
    except Exception:
        return False


def get_current_window_title() -> str:
    """Lấy tiêu đề cửa sổ đang active."""
    try:
        title = getActiveWindowTitle()
        if title:
            return title.strip()
    except Exception:
        pass
    try:
        hwnd = win32gui.GetForegroundWindow()
        if hwnd:
            return win32gui.GetWindowText(hwnd).strip()
    except Exception:
        pass
    return ""


import win32process


def is_real_genshin_window(hwnd: int) -> bool:
    """Kiểm tra cửa sổ có đúng là Genshin Impact không (loại trừ cửa sổ của chính tool)."""
    if not hwnd or not win32gui.IsWindow(hwnd) or not win32gui.IsWindowVisible(hwnd):
        return False
    try:
        _, pid = win32process.GetWindowThreadProcessId(hwnd)
        if pid == os.getpid():
            return False
    except Exception:
        pass
    title = win32gui.GetWindowText(hwnd).strip()
    t_lower = title.lower()
    if "auto-skip" in t_lower or "autoclick" in t_lower or "dialogue" in t_lower:
        return False
    if "genshin" in t_lower or "yuanshen" in t_lower or "原神" in title:
        return True
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
        is_windowed = bool(client_x > 0 or client_y > 0)
        is_fg = bool(target_hwnd == fg_hwnd)

        return is_fg, target_hwnd, target_title, client_x, client_y, client_w, client_h, is_windowed
    except Exception:
        return False, target_hwnd, target_title, 0, 0, 0, 0, False


class AutoSkipEngine:
    """Engine xử lý tự động nhận diện và tua hội thoại Genshin Impact đa độ phân giải & cửa sổ."""

    def __init__(self, config: Config):
        self.config = config
        self.status: str = "paused"  # "running", "paused", "stopped"
        self._stop_event = threading.Event()
        self._worker_thread: Optional[threading.Thread] = None
        self._listener: Optional[Listener] = None

        # Thống kê
        self.total_skips: int = 0
        self.total_choices: int = 0

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
        self.on_stats_update: Optional[Callable[[int, int], None]] = None  # (skips, choices)
        self.on_window_check: Optional[Callable[[bool, str, int, int, bool, int, int], None]] = None

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
        Hỗ trợ 16:9, 16:10 (như 1680x1050), 4:3, 5:4, UltraWide 21:9.
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

    # ========================== NHẬN DIỆN TRẠNG THÁI ==========================
    def is_dialogue_playing(self, screen_play_x: int, screen_play_y: int) -> bool:
        """Kiểm tra nút Auto Play với dải dung sai lân cận để tránh lệch pixel."""
        offsets = [(0, 0), (-3, 0), (3, 0), (0, -3), (0, 3), (-3, -3), (3, 3)]
        for dx, dy in offsets:
            try:
                px = pixel(screen_play_x + dx, screen_play_y + dy)
                if self.is_color_close(px, (236, 229, 216), tol=28):
                    return True
            except Exception:
                pass
        return False

    def is_dialogue_option_available(
        self,
        screen_load_x: int,
        screen_load_y: int,
        screen_diag_x: int,
        screen_lower_y: int,
        screen_higher_y: int,
    ) -> Tuple[bool, bool]:
        """Kiểm tra có lựa chọn hội thoại hay không."""
        # 1. Kiểm tra màn hình tải trắng
        try:
            load_px = pixel(screen_load_x, screen_load_y)
            if self.is_white_like(load_px, threshold=250):
                return False, False
        except Exception:
            pass

        # 2. Quét dải pixel dọc tại vị trí biểu tượng đối thoại
        mid_y = (screen_lower_y + screen_higher_y) // 2
        for target_y in [screen_lower_y, screen_higher_y, mid_y]:
            for off_x in [0, -3, 3]:
                for off_y in [0, -2, 2]:
                    try:
                        px = pixel(screen_diag_x + off_x, target_y + off_y)
                        if self.is_white_like(px, threshold=220):
                            return True, True
                    except Exception:
                        pass

        return False, False

    def send_key(self, key_char: str) -> None:
        try:
            pyautogui.keyDown(key_char)
            sleep(0.04)
            pyautogui.keyUp(key_char)
        except Exception as e:
            self.log(f"Lỗi khi nhấn phím '{key_char}': {e}", "warning")

    # ========================== VÒNG LẶP CHÍNH ==========================
    def _random_interval(self) -> float:
        if not self.config.human_simulation:
            return 0.12
        return uniform(0.18, 0.20) if randint(1, 6) == 6 else uniform(0.12, 0.18)

    def _should_take_break(self) -> bool:
        if not self.config.human_simulation:
            return False
        return randint(1, 25) == 1

    def _loop(self) -> None:
        last_press = 0.0
        next_interval = self._random_interval()
        last_break_check = perf_counter()
        break_check_interval = 30.0
        last_game_active: Optional[bool] = None

        while not self._stop_event.is_set():
            now = perf_counter()

            # Nếu đang pause
            if self.status == "paused":
                sleep(0.2)
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
                off_x, off_y = 0, 0

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

            # Chỉ ghi log khi thay đổi trạng thái chuyển tab game (tránh spam)
            if is_fg != last_game_active:
                last_game_active = is_fg
                if is_fg:
                    mode_str = "Cửa Sổ" if is_windowed else "Toàn Màn Hình"
                    pos_str = f" tại ({off_x}, {off_y})" if is_windowed else ""
                    self.log(f"Đã nhận diện Genshin Impact: {cur_w}x{cur_h} [{mode_str}]{pos_str}", "success")
                else:
                    self.log("Đang chờ chuyển sang cửa sổ Genshin Impact...", "info")

            if not is_fg:
                sleep(0.4)
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

            # 3. Kiểm tra hội thoại
            dialogue_playing = self.is_dialogue_playing(screen_play_x, screen_play_y)
            option_detected, is_choice = self.is_dialogue_option_available(
                screen_load_x, screen_load_y, screen_diag_x, screen_lower_y, screen_higher_y
            )
            dialogue_active = dialogue_playing or option_detected

            if not dialogue_active:
                sleep(0.08)
                continue

            # 4. Mô phỏng nghỉ ngơi ngẫu nhiên
            if now - last_break_check > break_check_interval:
                last_break_check = now
                if self._should_take_break():
                    break_sec = uniform(3.0, 7.0)
                    self.log(f"Tạm nghỉ {break_sec:.1f}s mô phỏng người thật...", "break")
                    sleep(break_sec)
                    last_press = perf_counter()
                    next_interval = self._random_interval()
                    continue

            # 5. Nhấn phím tương tác
            if now - last_press >= next_interval:
                confirm_key = self.config.confirm_button.lower()
                if is_choice:
                    self.total_choices += 1
                else:
                    self.total_skips += 1

                self.send_key(confirm_key)
                if self.on_stats_update:
                    self.on_stats_update(self.total_skips, self.total_choices)

                last_press = perf_counter()
                next_interval = self._random_interval()

            sleep(0.04)

    # ========================== ĐIỀU KHIỂN & PHÍM TẮT ==========================
    def start(self) -> None:
        """Kích hoạt chạy Auto-Skip."""
        self.status = "running"
        if self.on_status_change:
            self.on_status_change("running")
        self.log("BẮT ĐẦU: Auto-Skip đang hoạt động", "success")

    def pause(self) -> None:
        """Tạm dừng Auto-Skip."""
        self.status = "paused"
        if self.on_status_change:
            self.on_status_change("paused")
        self.log("TẠM DỪNG (Bấm F8 để tiếp tục)", "info")

    def toggle(self) -> None:
        """Chuyển đổi giữa chạy và tạm dừng."""
        if self.status == "running":
            self.pause()
        else:
            self.start()

    def reset_stats(self) -> None:
        self.total_skips = 0
        self.total_choices = 0
        if self.on_stats_update:
            self.on_stats_update(0, 0)

    def _on_key_press(self, key: Union[Key, KeyCode, None]) -> None:
        key_str = str(key)
        if key_str == "Key.f8":
            self.start()
        elif key_str == "Key.f9":
            self.pause()
        elif key_str == "Key.f12":
            self.stop()

    def run_in_background(self) -> None:
        """Khởi động worker thread và keyboard listener toàn cục."""
        self._stop_event.clear()
        self._worker_thread = threading.Thread(target=self._loop, daemon=True)
        self._worker_thread.start()

        try:
            self._listener = Listener(on_press=self._on_key_press)
            self._listener.start()
        except Exception as e:
            self.log(f"Không thể kích hoạt hook bàn phím toàn cục: {e}", "warning")

    def stop(self) -> None:
        """Dừng hoàn toàn engine."""
        self.status = "stopped"
        self._stop_event.set()
        if self._listener:
            try:
                self._listener.stop()
            except Exception:
                pass
        if self.on_status_change:
            self.on_status_change("stopped")
        self.log("ĐÃ DỪNG chương trình.", "info")
