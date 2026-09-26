import ctypes
import os
import sys
from random import randint, uniform
from threading import Thread
from time import perf_counter, sleep
from typing import Union
import win32gui
from win32api import GetSystemMetrics  # type: ignore[import-untyped]

import pyautogui  # type: ignore[import-untyped]
from pyautogui import getActiveWindowTitle, pixel  # type: ignore[import-untyped]
from pynput.keyboard import Key, KeyCode, Listener  # type: ignore[import-untyped]
from dotenv import find_dotenv, load_dotenv, set_key  # type: ignore[import-not-found]

# Đảm bảo nhận diện đúng tọa độ khi màn hình có bật Windows Display Scaling (125%, 150%, v.v.)
try:
    ctypes.windll.shcore.SetProcessDpiAwareness(2)
except Exception:
    try:
        ctypes.windll.user32.SetProcessDPIAware()
    except Exception:
        pass

# Đảm bảo hiển thị chuẩn tiếng Việt UTF-8 trong console Windows
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

def is_admin() -> bool:
    """Kiểm tra quyền Administrator của tiến trình."""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin() != 0
    except Exception:
        return False

# Khởi tạo màn hình và nạp cấu hình
os.system("cls")
load_dotenv()
print("\n" + "=" * 60)
print("  GENSHIN IMPACT - TỰ ĐỘNG BỎ QUA HỘI THOẠI (AUTO-SKIP)")
print("=" * 60)
print("  Phiên bản 1.0 | Bản Bàn phím & Chuột")
print("=" * 60 + "\n")

if not is_admin():
    print("  ⚠️  [CẢNH BÁO QUAN TRỌNG]:")
    print("  Tool hiện KHÔNG chạy với quyền Administrator!")
    print("  Genshin Impact có hệ thống bảo vệ sẽ CHẶN toàn bộ phím bấm từ tool.")
    print("  => Vui lòng nhấp chuột phải vào file 'run.bat' và chọn 'Run as administrator'!\n")
    print("-" * 60)
else:
    print("  [OK] Đang chạy với quyền Administrator.\n")


COORDS = {
    "gamepad": {
        "default": {}
    },
    "mnk": {
        "default": {
            "PLAYING_ICON_X": ("width_adjust", 84),
            "PLAYING_ICON_Y": ("height_adjust", 46),

            "DIALOGUE_ICON_X": ("width_adjust", 1301),
            "DIALOGUE_ICON_LOWER_Y": ("height_adjust", 808),
            "DIALOGUE_ICON_HIGHER_Y": ("height_adjust", 790),

            "LOADING_SCREEN_X": ("width_adjust", 1200),
            "LOADING_SCREEN_Y": ("height_adjust", 700)
        },
        "wide_screen": {
            "PLAYING_ICON_X": ("get_position_left", 84, 230),

            "DIALOGUE_ICON_X": ("get_position_right", 1301, 2770, 0.02),
            "DIALOGUE_ICON_LOWER_Y": ("height_adjust", 810),
            "DIALOGUE_ICON_HIGHER_Y": ("height_adjust", 792)
        },
        (2880, 1800): {
            "PLAYING_ICON_X": ("static", 126),

            "DIALOGUE_ICON_X": ("static", 1947),
            "DIALOGUE_ICON_LOWER_Y": ("static", 1370),
            "DIALOGUE_ICON_HIGHER_Y": ("static", 1260)
        }
    }
}


def width_adjust(x: int) -> int:
    """Tự động điều chỉnh tọa độ theo chiều rộng màn hình."""
    return int(x / 1920 * SCREEN_WIDTH)


def height_adjust(y: int) -> int:
    """Tự động điều chỉnh tọa độ theo chiều cao màn hình."""
    return int(y / 1080 * SCREEN_HEIGHT)


def get_position_right(
    hdpos_x: int, doublehdpos_x: int, SCREEN_WIDTH: int, extra: float
) -> int:
    if SCREEN_WIDTH <= 3840:
        extra = 0
    diff = doublehdpos_x - hdpos_x
    change_per_pixel = diff / 1920
    screen_diff = SCREEN_WIDTH - 1920
    extra_pixels = screen_diff * (change_per_pixel + extra)
    position = int(hdpos_x + extra_pixels)
    return position


def get_position_left(hdpos_x: int, doublehdpos_x: int, SCREEN_WIDTH: int) -> int:
    diff = doublehdpos_x - hdpos_x
    change_per_pixel = diff / 1920
    screen_diff = SCREEN_WIDTH - 1920
    extra_pixels = screen_diff * change_per_pixel
    position = int(hdpos_x + extra_pixels)
    return position


def is_screen_default_ratio() -> bool:
    if SCREEN_WIDTH > 1920 and float(int(SCREEN_HEIGHT) / int(SCREEN_WIDTH)) != float(0.5625):
        return False
    else:
        return True


def get_pixel(device: str, res: tuple[int, int], name: str):
    base = COORDS[device]["default"]
    override: dict = {}
    if res in COORDS[device]:
        override = COORDS[device].get(res, {})
    elif not is_screen_default_ratio():
        override = COORDS[device].get("wide_screen", {})

    merged = {**base, **override}

    if merged[name][0] == "width_adjust":
        return width_adjust(merged[name][1])
    if merged[name][0] == "height_adjust":
        return height_adjust(merged[name][1])
    if merged[name][0] == "get_position_left":
        x = get_position_left(merged[name][1], merged[name][2], res[0])
        if x > 231:
            x = 230
        return x
    if merged[name][0] == "get_position_right":
        return get_position_right(merged[name][1], merged[name][2], res[0], merged[name][3])
    if merged[name][0] == "static":
        return merged[name][1]

    raise ValueError(f"Không nhận diện được cấu hình tọa độ: {merged[name][0]} cho {device}.{name}")


# Kiểm tra cấu hình trong .env
if os.environ.get("WIDTH", "") == "" or os.environ.get("HEIGHT", "") == "" or os.environ.get("CONFIRM_BUTTON", "") == "" or os.environ.get("DEVICE", "") == "":
    SCREEN_WIDTH = GetSystemMetrics(0)
    SCREEN_HEIGHT = GetSystemMetrics(1)
    CONFIRM_BUTTON = "f"
    DEVICE = "mnk"

    print(f"  Độ phân giải màn hình phát hiện được: {SCREEN_WIDTH}x{SCREEN_HEIGHT}\n")

    while True:
        temp_conf_btn = str(input("Nhập phím tương tác trong game của bạn (mặc định F): ").strip())
        if temp_conf_btn == "":
            CONFIRM_BUTTON = "f"
            break
        elif len(temp_conf_btn) == 1:
            CONFIRM_BUTTON = str(temp_conf_btn.lower())
            break
        else:
            print("Định dạng không hợp lệ. Vui lòng chỉ nhập đúng 1 ký tự.")

    dotenv_file = find_dotenv()
    if dotenv_file:
        set_key(dotenv_file, "WIDTH", str(SCREEN_WIDTH), quote_mode="never")
        set_key(dotenv_file, "HEIGHT", str(SCREEN_HEIGHT), quote_mode="never")
        set_key(dotenv_file, "CONFIRM_BUTTON", str(CONFIRM_BUTTON), quote_mode="never")
        set_key(dotenv_file, "DEVICE", str(DEVICE), quote_mode="never")
    else:
        with open(".env", "w", encoding="utf-8") as f:
            f.write(f"WIDTH={SCREEN_WIDTH}\n")
            f.write(f"HEIGHT={SCREEN_HEIGHT}\n")
            f.write(f"CONFIRM_BUTTON={CONFIRM_BUTTON}\n")
            f.write(f"DEVICE={DEVICE}\n")
else:
    width_str = os.getenv("WIDTH")
    height_str = os.getenv("HEIGHT")
    if width_str is None or height_str is None:
        raise ValueError("Biến môi trường WIDTH hoặc HEIGHT không hợp lệ")
    SCREEN_WIDTH = int(width_str)
    SCREEN_HEIGHT = int(height_str)

    CONFIRM_BUTTON = os.getenv("CONFIRM_BUTTON", "f")
    DEVICE = os.getenv("DEVICE", "mnk")

    print(f"  Độ phân giải hiện tại: {SCREEN_WIDTH}x{SCREEN_HEIGHT}")
    print(f"  Thiết bị điều khiển: {DEVICE}")
    print(f"  Phím tương tác: {CONFIRM_BUTTON}\n")

res = (SCREEN_WIDTH, SCREEN_HEIGHT)


def random_f_key_interval() -> float:
    return uniform(0.18, 0.2) if randint(1, 6) == 6 else uniform(0.12, 0.18)


def should_take_break() -> bool:
    return randint(1, 25) == 1


def take_random_break() -> float:
    break_duration = uniform(3.0, 8.0)
    print(f"  [Nghỉ giải lao] Tạm dừng {break_duration:.1f}s để mô phỏng hành vi người thật...")
    return break_duration


class MainStatus:
    def __init__(self) -> None:
        self.status: str = "pause"


main_status = MainStatus()


def on_press(key: Union[Key, KeyCode, None]) -> None:
    key_pressed = str(key)

    if key_pressed == "Key.f8":
        main_status.status = "run"
        print("\n" + "=" * 50)
        print("  TRẠNG THÁI: ĐANG CHẠY (RUNNING)")
        print("  Tự động bỏ qua hội thoại: ĐÃ KÍCH HOẠT")
        print("=" * 50 + "\n")
    elif key_pressed == "Key.f9":
        main_status.status = "pause"
        print("\n" + "=" * 50)
        print("  TRẠNG THÁI: TẠM DỪNG (PAUSED)")
        print("  Tự động bỏ qua hội thoại: ĐÃ TẠM DỪNG")
        print("=" * 50 + "\n")
    elif key_pressed == "Key.f12":
        main_status.status = "exit"
        print("\n" + "=" * 50)
        print("  Đang tắt chương trình... Hẹn gặp lại!")
        print("=" * 50 + "\n")
        exit()


def is_color_close(c1, c2, tol: int = 25) -> bool:
    """So sánh 2 màu RGB kèm độ lệch dung sai (tolerance)."""
    if not c1 or not c2:
        return False
    return (
        abs(c1[0] - c2[0]) <= tol and
        abs(c1[1] - c2[1]) <= tol and
        abs(c1[2] - c2[2]) <= tol
    )


def is_white_like(c, threshold: int = 230) -> bool:
    """Kiểm tra màu có tiệm cận màu trắng hay không."""
    if not c:
        return False
    return c[0] >= threshold and c[1] >= threshold and c[2] >= threshold


def send_key(key_char: str) -> None:
    """Gửi phím tương tác với độ giữ 40ms để game nhận diện chuẩn qua DirectX."""
    try:
        pyautogui.keyDown(key_char)
        sleep(0.04)
        pyautogui.keyUp(key_char)
    except Exception as e:
        print(f"\n  [Lỗi phím]: Không thể nhấn phím {key_char}: {e}")


def get_current_window_title() -> str:
    """Lấy tiêu đề của cửa sổ đang kích hoạt (hỗ trợ cả getActiveWindowTitle và win32gui)."""
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


def main() -> None:
    def is_genshin_impact_active() -> tuple[bool, str]:
        """Kiểm tra xem cửa sổ Genshin Impact có đang active hay không."""
        title = get_current_window_title()
        t_lower = title.lower()
        is_active = bool(
            "genshin" in t_lower or
            "yuanshen" in t_lower or
            "原神" in title
        )
        return is_active, title

    def is_dialogue_playing() -> tuple[bool, bool]:
        """Kiểm tra nút Auto Play (góc trên bên trái màn hình)."""
        try:
            current_pixel = pixel(get_pixel(DEVICE, res, "PLAYING_ICON_X"), get_pixel(DEVICE, res, "PLAYING_ICON_Y"))
            # Màu mặc định của nút Auto là (236, 229, 216), cho phép sai lệch dung sai tol=25
            return is_color_close(current_pixel, (236, 229, 216), tol=25), False
        except Exception:
            return False, False

    def is_dialogue_option_available() -> tuple[bool, bool]:
        """Kiểm tra xem có danh sách lựa chọn hội thoại trên màn hình hay không."""
        try:
            # Nếu đang ở màn hình tải (trắng xóa) thì không bấm
            load_px = pixel(get_pixel(DEVICE, res, "LOADING_SCREEN_X"), get_pixel(DEVICE, res, "LOADING_SCREEN_Y"))
            if is_white_like(load_px, threshold=250):
                return False, False

            # Kiểm tra biểu tượng hội thoại bên dưới
            lower_px = pixel(get_pixel(DEVICE, res, "DIALOGUE_ICON_X"), get_pixel(DEVICE, res, "DIALOGUE_ICON_LOWER_Y"))
            if is_white_like(lower_px, threshold=225):
                return True, True

            # Kiểm tra biểu tượng hội thoại bên trên
            higher_px = pixel(get_pixel(DEVICE, res, "DIALOGUE_ICON_X"), get_pixel(DEVICE, res, "DIALOGUE_ICON_HIGHER_Y"))
            if is_white_like(higher_px, threshold=225):
                return True, True

            return False, False
        except Exception:
            return False, False

    main_status.status = "pause"
    last_f_press = 0.0
    next_f_interval = random_f_key_interval()

    last_break_check = perf_counter()
    break_check_interval = 30.0

    last_log_state = ""
    last_log_time = 0.0

    def log_status(msg: str, throttle_sec: float = 3.0):
        nonlocal last_log_state, last_log_time
        now = perf_counter()
        if msg != last_log_state or (now - last_log_time) >= throttle_sec:
            last_log_state = msg
            last_log_time = now
            print(f"  {msg}")

    print("\n" + "=" * 60)
    print("  ĐÃ SẴN SÀNG HOẠT ĐỘNG")
    print("=" * 60)
    print("  Phím tắt điều khiển:")
    print("    [F8]  - Bật / Chạy Auto-Skip")
    print("    [F9]  - Tạm dừng Auto-Skip")
    print("    [F12] - Thoát chương trình")
    print("=" * 60)
    print("\n  Đang chờ lệnh... Hãy vào Genshin Impact và nhấn F8 để bắt đầu!\n")

    while True:
        current_time = perf_counter()

        while main_status.status == "pause":
            sleep(0.5)
            current_time = perf_counter()
            last_f_press = current_time

        if main_status.status == "exit":
            break

        # Kiểm tra cửa sổ Genshin Impact
        genshin_active, current_title = is_genshin_impact_active()
        if not genshin_active:
            display_title = current_title if current_title else "Không xác định"
            log_status(f"[Chờ cửa sổ game...] Cửa sổ hiện tại: '{display_title}' (Hãy chuyển sang Genshin Impact)", throttle_sec=3.0)
            sleep(0.5)
            continue

        # Kiểm tra hội thoại
        dialogue_playing, _ = is_dialogue_playing()
        option_detected, option_choice = is_dialogue_option_available()
        dialogue_active = dialogue_playing or option_detected

        if not dialogue_active:
            log_status("[Đang giám sát...] Đã nhận diện Genshin Impact, đang chờ xuất hiện đoạn thoại...", throttle_sec=4.0)
            sleep(0.08)
            continue

        # Xử lý nghỉ ngơi mô phỏng người thật
        if current_time - last_break_check > break_check_interval:
            last_break_check = current_time
            if should_take_break():
                break_duration = take_random_break()
                sleep(break_duration)
                last_f_press = perf_counter()
                next_f_interval = random_f_key_interval()
                continue

        # Nhấn phím tương tác
        if current_time - last_f_press >= next_f_interval:
            if option_choice:
                log_status(f"🎯 [Phát hiện lựa chọn câu hỏi!] -> Tự động nhấn '{CONFIRM_BUTTON}' để chọn đáp án", throttle_sec=1.0)
            else:
                log_status(f"⏩ [Đang tua hội thoại...] -> Nhấn '{CONFIRM_BUTTON}'", throttle_sec=1.0)

            send_key(CONFIRM_BUTTON)

            last_f_press = current_time
            next_f_interval = random_f_key_interval()

        sleep(0.04)


if __name__ == "__main__":
    Thread(target=main).start()

    with Listener(on_press=on_press) as listener:
        listener.join()
