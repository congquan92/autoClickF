import datetime
import os
import queue
import re
import sys
import threading
import tkinter as tk
from typing import Any, Tuple

import customtkinter as ctk

from core.config import Config, get_screen_resolution
from core.engine import AutoSkipEngine, get_genshin_window_info, is_admin

# Thiết lập theme mặc định cho giao diện
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

RESOLUTION_PRESETS = [
    "🎯 Tự động (Theo game)",
    "1680×1050 (Cửa Sổ 16:10)",
    "1920×1080 (Toàn Màn Hình)",
    "1440×1080 (Cửa Sổ 4:3)",
    "1440×900 (Cửa Sổ 16:10)",
    "1366×768 (Cửa Sổ 16:9)",
    "1360×768 (Cửa Sổ 16:9)",
    "1280×1024 (Cửa Sổ 5:4)",
    "1280×800 (Cửa Sổ 16:10)",
    "1280×768 (Cửa Sổ 5:3)",
    "1280×720 (Cửa Sổ 16:9)",
    "1176×664 (Cửa Sổ 16:9)",
    "2560×1440 (2K 16:9)",
    "3840×2160 (4K 16:9)",
    "2560×1080 (UltraWide 21:9)",
    "3440×1440 (UltraWide 21:9)",
]


class AutoSkipGUI(ctk.CTk):
    """Giao diện đồ họa nhỏ gọn (Mini Widget) hỗ trợ toàn diện Genshin Impact."""

    def __init__(self):
        super().__init__()

        # Nạp cấu hình
        self.config = Config()
        self.engine = AutoSkipEngine(self.config)

        # Hàng đợi giao tiếp thread-safe giữa Engine và GUI
        self.event_queue: queue.Queue = queue.Queue()

        # Cài đặt cửa sổ chính mini
        self.title("Genshin Auto-Skip")
        self.geometry("380x420")
        self.minsize(360, 400)
        self.configure(fg_color="#0f172a")  # Slate 900 background

        # Áp dụng ghim cửa sổ theo config
        self.wm_attributes("-topmost", self.config.always_on_top)

        # Kết nối callback của Engine tới Queue
        self.engine.on_status_change = lambda status: self.event_queue.put(("status", status))
        self.engine.on_log = lambda msg, cat: self.event_queue.put(("log", (msg, cat)))
        self.engine.on_stats_update = lambda s, c: self.event_queue.put(("stats", (s, c)))
        self.engine.on_window_check = (
            lambda act, title, w, h, win_mode, ox, oy: self.event_queue.put(
                ("window", (act, title, w, h, win_mode, ox, oy))
            )
        )

        # Xây dựng các thành phần giao diện gọn gàng
        self._build_ui()

        # Thông báo khởi động ngắn gọn
        self._append_log("Đã sẵn sàng. Bấm [F8] để bắt đầu tua thoại.", "info")

        # Bắt đầu Engine chạy ngầm
        self.engine.run_in_background()

        # Bắt đầu xử lý hàng đợi sự kiện định kỳ (50ms)
        self.after(50, self._process_events)

        # Xử lý đóng ứng dụng an toàn
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    def _build_ui(self):
        self.main_container = ctk.CTkFrame(self, fg_color="transparent")
        self.main_container.pack(fill="both", expand=True, padx=10, pady=8)

        # 1. THẺ TRẠNG THÁI SỐNG (HERO CARD COMPACT)
        self._build_status_card()

        # 2. NÚT ĐIỀU KHIỂN CHÍNH (CONTROLS COMPACT)
        self._build_controls()

        # 3. CÀI ĐẶT NHANH (SETTINGS COMPACT)
        self._build_settings_card()

        # 4. HỘP THÔNG BÁO HỆ THỐNG (LOG MINI)
        self._build_log_view()

    # ========================== GIAO DIỆN COMPACT ==========================
    def _build_status_card(self):
        self.status_card = ctk.CTkFrame(
            self.main_container,
            fg_color="#1e293b",
            corner_radius=10,
            border_width=1,
            border_color="#334155"
        )
        self.status_card.pack(fill="x", pady=(0, 6))

        # Dòng 1: Status indicator + Admin badge
        row1 = ctk.CTkFrame(self.status_card, fg_color="transparent")
        row1.pack(fill="x", padx=10, pady=(8, 2))

        self.status_indicator = ctk.CTkLabel(
            row1,
            text="⏸️ TẠM DỪNG (F9)",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color="#f59e0b"
        )
        self.status_indicator.pack(side="left")

        # Admin status badge nhỏ gọn
        has_admin = is_admin()
        admin_text = "🛡️ Admin: OK" if has_admin else "⚠️ No Admin"
        admin_color = "#34d399" if has_admin else "#f87171"
        admin_bg = "#064e3b" if has_admin else "#7f1d1d"

        self.admin_badge = ctk.CTkLabel(
            row1,
            text=admin_text,
            font=ctk.CTkFont(size=10, weight="bold"),
            text_color=admin_color,
            fg_color=admin_bg,
            corner_radius=4,
            padx=6,
            pady=2
        )
        self.admin_badge.pack(side="right")

        # Dòng 2: Trạng thái cửa sổ game
        self.game_status_label = ctk.CTkLabel(
            self.status_card,
            text="🎮 Cửa sổ: Đang chờ mở Genshin Impact...",
            font=ctk.CTkFont(size=11),
            text_color="#cbd5e1",
            anchor="w"
        )
        self.game_status_label.pack(fill="x", padx=10, pady=(0, 4))

        # Dòng 3: Thống kê số lần tua & chọn
        stats_frame = ctk.CTkFrame(self.status_card, fg_color="#0f172a", corner_radius=6)
        stats_frame.pack(fill="x", padx=8, pady=(0, 8))

        self.skip_counter_label = ctk.CTkLabel(
            stats_frame,
            text="⏩ Tua: 0",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color="#38bdf8"
        )
        self.skip_counter_label.pack(side="left", expand=True, pady=4)

        sep = ctk.CTkFrame(stats_frame, width=1, height=14, fg_color="#334155")
        sep.pack(side="left", pady=2)

        self.choice_counter_label = ctk.CTkLabel(
            stats_frame,
            text="🎯 Chọn: 0",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color="#fbbf24"
        )
        self.choice_counter_label.pack(side="left", expand=True, pady=4)

        sep2 = ctk.CTkFrame(stats_frame, width=1, height=14, fg_color="#334155")
        sep2.pack(side="left", pady=2)

        self.res_badge = ctk.CTkLabel(
            stats_frame,
            text=f"📐 {self.config.width}x{self.config.height}",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color="#93c5fd"
        )
        self.res_badge.pack(side="left", expand=True, pady=4)

    def _build_controls(self):
        ctrl_frame = ctk.CTkFrame(self.main_container, fg_color="transparent")
        ctrl_frame.pack(fill="x", pady=(0, 6))

        self.btn_start = ctk.CTkButton(
            ctrl_frame,
            text="▶ BẮT ĐẦU (F8)",
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color="#16a34a",
            hover_color="#15803d",
            height=32,
            corner_radius=6,
            command=self._on_start_click
        )
        self.btn_start.pack(side="left", fill="x", expand=True, padx=(0, 4))

        self.btn_pause = ctk.CTkButton(
            ctrl_frame,
            text="⏸ TẠM DỪNG (F9)",
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color="#d97706",
            hover_color="#b45309",
            height=32,
            corner_radius=6,
            command=self._on_pause_click
        )
        self.btn_pause.pack(side="left", fill="x", expand=True, padx=(4, 0))

    def _build_settings_card(self):
        settings_card = ctk.CTkFrame(
            self.main_container,
            fg_color="#1e293b",
            corner_radius=10,
            border_width=1,
            border_color="#334155"
        )
        settings_card.pack(fill="x", pady=(0, 6))

        # Dòng 1: Phím + Dropdown màn hình + Nút Quét
        row1 = ctk.CTkFrame(settings_card, fg_color="transparent")
        row1.pack(fill="x", padx=8, pady=(6, 4))

        ctk.CTkLabel(row1, text="Phím:", font=ctk.CTkFont(size=11)).pack(side="left")
        self.key_combo = ctk.CTkComboBox(
            row1,
            values=["F", "Space", "E", "Enter"],
            width=65,
            height=26,
            font=ctk.CTkFont(size=11),
            command=self._on_key_change
        )
        self.key_combo.set(self.config.confirm_button.upper())
        self.key_combo.pack(side="left", padx=(4, 6))

        self.res_combo = ctk.CTkComboBox(
            row1,
            values=RESOLUTION_PRESETS,
            width=150,
            height=26,
            font=ctk.CTkFont(size=11),
            command=self._on_res_preset_change
        )
        self._init_res_combo_selection()
        self.res_combo.pack(side="left", fill="x", expand=True, padx=(0, 6))

        btn_scan = ctk.CTkButton(
            row1,
            text="🔍 Quét",
            font=ctk.CTkFont(size=11, weight="bold"),
            width=58,
            height=26,
            fg_color="#2563eb",
            hover_color="#1d4ed8",
            command=self._on_scan_game
        )
        btn_scan.pack(side="right")

        # Dòng 2: Switches thu gọn
        row2 = ctk.CTkFrame(settings_card, fg_color="transparent")
        row2.pack(fill="x", padx=8, pady=(0, 6))

        self.switch_topmost = ctk.CTkSwitch(
            row2,
            text="Ghim trên cùng",
            font=ctk.CTkFont(size=11),
            command=self._on_topmost_toggle
        )
        if self.config.always_on_top:
            self.switch_topmost.select()
        else:
            self.switch_topmost.deselect()
        self.switch_topmost.pack(side="left")

        self.switch_human = ctk.CTkSwitch(
            row2,
            text="Mô phỏng người",
            font=ctk.CTkFont(size=11),
            command=self._on_human_toggle
        )
        if self.config.human_simulation:
            self.switch_human.select()
        else:
            self.switch_human.deselect()
        self.switch_human.pack(side="right")

    def _init_res_combo_selection(self):
        if self.config.auto_window_mode:
            self.res_combo.set(RESOLUTION_PRESETS[0])
            return

        w, h = self.config.width, self.config.height
        matched = False
        for p in RESOLUTION_PRESETS:
            if f"{w}×{h}" in p or f"{w}x{h}" in p:
                self.res_combo.set(p)
                matched = True
                break
        if not matched:
            self.res_combo.set(f"Tuỳ chỉnh ({w}x{h})")

    def _build_log_view(self):
        log_card = ctk.CTkFrame(
            self.main_container,
            fg_color="#1e293b",
            corner_radius=10,
            border_width=1,
            border_color="#334155"
        )
        log_card.pack(fill="both", expand=True)

        log_header = ctk.CTkFrame(log_card, fg_color="transparent")
        log_header.pack(fill="x", padx=8, pady=(4, 2))

        ctk.CTkLabel(
            log_header,
            text="📋 Thông Báo",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color="#e2e8f0"
        ).pack(side="left")

        btn_clear = ctk.CTkButton(
            log_header,
            text="Xóa",
            font=ctk.CTkFont(size=10),
            width=42,
            height=20,
            fg_color="#334155",
            hover_color="#475569",
            command=self._clear_logs
        )
        btn_clear.pack(side="right")

        btn_reset_stats = ctk.CTkButton(
            log_header,
            text="Reset",
            font=ctk.CTkFont(size=10),
            width=48,
            height=20,
            fg_color="#334155",
            hover_color="#475569",
            command=self._reset_counters
        )
        btn_reset_stats.pack(side="right", padx=(0, 4))

        self.log_text = ctk.CTkTextbox(
            log_card,
            fg_color="#090d16",
            text_color="#cbd5e1",
            font=ctk.CTkFont(family="Consolas", size=10),
            corner_radius=6,
            border_width=1,
            border_color="#1e293b",
            height=85
        )
        self.log_text.pack(fill="both", expand=True, padx=8, pady=(0, 6))
        self.log_text.configure(state="disabled")

    # ========================== XỬ LÝ SỰ KIỆN ==========================
    def _process_events(self):
        """Đọc và xử lý các sự kiện từ Engine gửi qua queue (thread-safe)."""
        try:
            while not self.event_queue.empty():
                event_type, payload = self.event_queue.get_nowait()
                if event_type == "status":
                    self._update_status_ui(payload)
                elif event_type == "log":
                    msg, cat = payload
                    self._append_log(msg, cat)
                elif event_type == "stats":
                    skips, choices = payload
                    self._update_stats_ui(skips, choices)
                elif event_type == "window":
                    act, title, cur_w, cur_h, is_win, ox, oy = payload
                    self._update_window_ui(act, title, cur_w, cur_h, is_win, ox, oy)
        except Exception as e:
            print(f"Lỗi xử lý hàng đợi sự kiện: {e}")

        self.after(50, self._process_events)

    def _update_status_ui(self, status: str):
        if status == "running":
            self.status_card.configure(border_color="#10b981", fg_color="#064e3b")
            self.status_indicator.configure(text="🟢 ĐANG CHẠY (F8)", text_color="#34d399")
        elif status == "paused":
            self.status_card.configure(border_color="#f59e0b", fg_color="#1e293b")
            self.status_indicator.configure(text="⏸️ TẠM DỪNG (F9)", text_color="#f59e0b")
        elif status == "stopped":
            self.status_card.configure(border_color="#64748b", fg_color="#1e293b")
            self.status_indicator.configure(text="⚪ ĐÃ DỪNG", text_color="#94a3b8")

    def _update_stats_ui(self, skips: int, choices: int):
        self.skip_counter_label.configure(text=f"⏩ Tua: {skips}")
        self.choice_counter_label.configure(text=f"🎯 Chọn: {choices}")

    def _update_window_ui(self, is_active: bool, title: str, cur_w: int, cur_h: int, is_windowed: bool, ox: int, oy: int):
        mode_str = "Cửa Sổ" if is_windowed else "Toàn Màn Hình"

        if is_active:
            self.game_status_label.configure(
                text=f"🎮 Genshin: {cur_w}x{cur_h} [{mode_str}] (Active)",
                text_color="#6ee7b7"
            )
            self.res_badge.configure(text=f"📐 {cur_w}x{cur_h}")
        else:
            if cur_w > 0 and title:
                self.game_status_label.configure(
                    text=f"🎮 Genshin: {cur_w}x{cur_h} [{mode_str}] (Chờ active)",
                    text_color="#fcd34d"
                )
                self.res_badge.configure(text=f"📐 {cur_w}x{cur_h}")
            else:
                self.game_status_label.configure(
                    text="🎮 Cửa sổ: Đang chờ mở Genshin Impact...",
                    text_color="#fcd34d"
                )

    def _append_log(self, msg: str, category: str):
        icons = {
            "info": "ℹ️",
            "success": "✅",
            "skip": "⏩",
            "choice": "🎯",
            "break": "☕",
            "warning": "⚠️",
        }
        icon = icons.get(category, "•")
        time_str = datetime.datetime.now().strftime("%H:%M:%S")
        formatted_entry = f"[{time_str}] {icon} {msg}\n"

        self.log_text.configure(state="normal")
        self.log_text.insert("end", formatted_entry)

        # Giới hạn tối đa 30 dòng thông báo gần nhất để giao diện siêu nhẹ
        lines = int(self.log_text.index("end-1c").split(".")[0])
        if lines > 30:
            self.log_text.delete("1.0", "2.0")

        self.log_text.see("end")
        self.log_text.configure(state="disabled")

    def _clear_logs(self):
        self.log_text.configure(state="normal")
        self.log_text.delete("1.0", "end")
        self.log_text.configure(state="disabled")

    def _reset_counters(self):
        self.engine.reset_stats()
        self._update_stats_ui(0, 0)
        self._append_log("Đã đặt lại bộ đếm tua thoại và câu hỏi.", "info")

    # ========================== CALLBACKS NGƯỜI DÙNG ==========================
    def _on_start_click(self):
        self.engine.start()

    def _on_pause_click(self):
        self.engine.pause()

    def _on_key_change(self, value: str):
        btn = value.strip().lower()
        self.config.save(confirm_button=btn)
        self._append_log(f"Đã đổi phím: [{btn.upper()}]", "info")

    def _on_res_preset_change(self, selected: str):
        if "Tự động" in selected:
            self.config.save(auto_window_mode=True, resolution_preset="auto")
            self._append_log("Đã bật: Tự động theo cửa sổ game", "success")
            return

        match = re.search(r"(\d+)[\xd7x](\d+)", selected)
        if match:
            w = int(match.group(1))
            h = int(match.group(2))
            self.config.save(width=w, height=h, auto_window_mode=False, resolution_preset=selected)
            self.res_badge.configure(text=f"📐 {w}x{h}")
            self._append_log(f"Đã chọn độ phân giải: {w}x{h}", "info")

    def _on_scan_game(self):
        """Quét và tìm kiếm cửa sổ Genshin Impact thực tế."""
        is_fg, hwnd, title, client_x, client_y, client_w, client_h, is_windowed = get_genshin_window_info()
        if hwnd and client_w > 100 and client_h > 100:
            mode = "Cửa Sổ" if is_windowed else "Toàn Màn Hình"
            pos = f" tại ({client_x}, {client_y})" if is_windowed else ""
            self.config.save(width=client_w, height=client_h)
            self.res_badge.configure(text=f"📐 {client_w}x{client_h}")

            matched = False
            for p in RESOLUTION_PRESETS:
                if f"{client_w}×{client_h}" in p or f"{client_w}x{client_h}" in p:
                    self.res_combo.set(p)
                    matched = True
                    break
            if not matched and not self.config.auto_window_mode:
                self.res_combo.set(f"Tuỳ chỉnh ({client_w}x{client_h})")

            self._append_log(f"Đã tìm thấy game: {client_w}x{client_h} [{mode}]{pos}", "success")
        else:
            w, h = get_screen_resolution()
            self.config.save(width=w, height=h)
            self.res_badge.configure(text=f"📐 {w}x{h}")
            self._append_log(f"Chưa mở game. Đã nhận diện màn hình: {w}x{h}", "info")

    def _on_topmost_toggle(self):
        is_top = bool(self.switch_topmost.get())
        self.wm_attributes("-topmost", is_top)
        self.config.save(always_on_top=is_top)
        msg = "Đã ghim cửa sổ trên cùng" if is_top else "Đã bỏ ghim cửa sổ"
        self._append_log(msg, "info")

    def _on_human_toggle(self):
        is_human = bool(self.switch_human.get())
        self.config.save(human_simulation=is_human)
        msg = "Đã bật mô phỏng người thật" if is_human else "Đã tắt mô phỏng"
        self._append_log(msg, "info")

    def _on_close(self):
        self.engine.stop()
        self.destroy()
        sys.exit(0)


def main():
    app = AutoSkipGUI()
    app.mainloop()


if __name__ == "__main__":
    main()
