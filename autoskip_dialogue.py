import os
import sys
import time

from core.config import Config
from core.engine import AutoSkipEngine, is_admin

# Đảm bảo hiển thị chuẩn tiếng Việt UTF-8 trong console Windows
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass


def main():
    os.system("cls")
    print("\n" + "=" * 60)
    print("  GENSHIN IMPACT - TỰ ĐỘNG BỎ QUA HỘI THOẠI (AUTO-SKIP)")
    print("=" * 60)
    print("  Phiên bản 1.0 | Chế độ Dòng lệnh (CLI)")
    print("=" * 60 + "\n")

    if not is_admin():
        print("  ⚠️  [CẢNH BÁO QUAN TRỌNG]:")
        print("  Tool hiện KHÔNG chạy với quyền Administrator!")
        print("  Genshin Impact có hệ thống bảo vệ sẽ CHẶN toàn bộ phím bấm từ tool.")
        print("  => Vui lòng nhấp chuột phải vào file 'run.bat' và chọn 'Run as administrator'!\n")
        print("-" * 60)
    else:
        print("  [OK] Đang chạy với quyền Administrator.\n")

    config = Config()

    print(f"  Độ phân giải hiện tại: {config.width}x{config.height}")
    print(f"  Thiết bị điều khiển: {config.device}")
    print(f"  Phím tương tác: {config.confirm_button}\n")

    engine = AutoSkipEngine(config)

    def on_status_change(status: str):
        if status == "running":
            print("\n" + "=" * 50)
            print("  TRẠNG THÁI: ĐANG CHẠY (RUNNING)")
            print("  Tự động bỏ qua hội thoại: ĐÃ KÍCH HOẠT")
            print("=" * 50 + "\n")
        elif status == "paused":
            print("\n" + "=" * 50)
            print("  TRẠNG THÁI: TẠM DỪNG (PAUSED)")
            print("  Tự động bỏ qua hội thoại: ĐÃ TẠM DỪNG")
            print("=" * 50 + "\n")
        elif status == "stopped":
            print("\n" + "=" * 50)
            print("  Đang tắt chương trình... Hẹn gặp lại!")
            print("=" * 50 + "\n")

    engine.on_status_change = on_status_change
    engine.on_log = lambda msg, cat: print(f"  {msg}")

    print("\n" + "=" * 60)
    print("  ĐÃ SẴN SÀNG HOẠT ĐỘNG")
    print("=" * 60)
    print("  Phím tắt điều khiển:")
    print("    [F8]  - Bật / Chạy Auto-Skip")
    print("    [F9]  - Tạm dừng Auto-Skip")
    print("    [F12] - Thoát chương trình")
    print("=" * 60)
    print("\n  Đang chờ lệnh... Hãy vào Genshin Impact và nhấn F8 để bắt đầu!\n")

    engine.run_in_background()

    try:
        while engine.status != "stopped":
            time.sleep(0.3)
    except KeyboardInterrupt:
        engine.stop()


if __name__ == "__main__":
    main()
