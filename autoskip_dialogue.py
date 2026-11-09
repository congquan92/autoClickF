import os
import sys
import time

from core.config import Config
from core.engine import AutoSkipEngine, format_key_display, is_admin

# Đảm bảo hiển thị chuẩn tiếng Việt UTF-8 trong console Windows
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass


def main():
    os.system("cls")
    print("\n" + "=" * 62)
    print("  GENSHIN IMPACT - TỰ ĐỘNG BỎ QUA HỘI THOẠI (AUTO-SKIP TURBO)")
    print("=" * 62)
    print("  Phiên bản 2.0 | Chế độ Dòng lệnh (CLI) Tốc Độ Cao")
    print("=" * 62 + "\n")

    if not is_admin():
        print("  ⚠️  [CẢNH BÁO QUAN TRỌNG]:")
        print("  Tool hiện KHÔNG chạy với quyền Administrator!")
        print("  Genshin Impact có hệ thống bảo vệ sẽ CHẶN toàn bộ phím bấm từ tool.")
        print("  => Vui lòng nhấp chuột phải vào file 'run.bat' và chọn 'Run as administrator'!\n")
        print("-" * 62)
    else:
        print("  [OK] Đang chạy với quyền Administrator.\n")

    config = Config()

    mode_names = {
        "safe": "🐢 An toàn (Mô phỏng người thật, ~5 lần/giây)",
        "fast": "⚡ Nhanh (Đều đặn, ~15-20 lần/giây)",
        "turbo": "🚀 Siêu tốc (Spam liên hồi, ~40-60 lần/giây)",
        "extreme": "💥 Cực hạn (Tối đa phần cứng, ~100+ lần/giây)"
    }
    mode_display = mode_names.get(config.spam_mode, config.spam_mode)
    trigger_display = "⚡ Luôn spam trong game (Loot & Skip)" if config.trigger_mode == "always" else "💬 Chỉ khi phát hiện hội thoại"

    start_disp = format_key_display(config.hotkey_start)
    pause_disp = format_key_display(config.hotkey_pause)

    print(f"  Độ phân giải màn hình: {config.width}x{config.height}")
    print(f"  Phím tương tác:        [{config.confirm_button.upper()}]")
    print(f"  Phím tắt Bắt đầu:      [{start_disp}]")
    print(f"  Phím tắt Tạm dừng:     [{pause_disp}]")
    print(f"  Chế độ tốc độ:         {mode_display}")
    print(f"  Cách thức kích hoạt:   {trigger_display}")
    print(f"  Số lần spam mỗi nhịp:  {config.burst_count}x")
    print(f"  Kèm Click chuột trái:  {'BẬT' if config.click_combo else 'TẮT'}\n")

    engine = AutoSkipEngine(config)

    def on_status_change(status: str):
        if status == "running":
            print("\n" + "=" * 50)
            print("  TRẠNG THÁI: ĐANG CHẠY (RUNNING)")
            print(f"  Tốc độ: {config.spam_mode.upper()} | Nhịp: {config.burst_count}x")
            print("=" * 50 + "\n")
        elif status == "paused":
            print("\n" + "=" * 50)
            print("  TRẠNG THÁI: TẠM DỪNG (PAUSED)")
            print(f"  Nhấn [{start_disp}] để tiếp tục tua thoại.")
            print("=" * 50 + "\n")
        elif status == "stopped":
            print("\n" + "=" * 50)
            print("  Đang tắt chương trình... Hẹn gặp lại!")
            print("=" * 50 + "\n")

    engine.on_status_change = on_status_change
    engine.on_log = lambda msg, cat: print(f"  {msg}")

    print("=" * 62)
    print("  ĐÃ SẴN SÀNG HOẠT ĐỘNG")
    print("=" * 62)
    print("  Phím tắt điều khiển:")
    print(f"    [{start_disp:<4}] - Bật / Chạy Auto-Skip")
    print(f"    [{pause_disp:<4}] - Tạm dừng Auto-Skip")
    print("    [F12 ] - Thoát chương trình")
    print("=" * 62)
    print(f"\n  Đang chờ lệnh... Hãy vào Genshin Impact và nhấn {start_disp} để bắt đầu!\n")

    engine.run_in_background()

    try:
        while engine.status != "stopped":
            time.sleep(0.3)
    except KeyboardInterrupt:
        engine.stop()


if __name__ == "__main__":
    main()
