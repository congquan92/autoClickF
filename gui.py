import datetime
import queue
import re
from typing import Optional

import customtkinter as ctk

from core.config import Config, get_screen_resolution
from core.engine import (
    AutoSkipEngine,
    format_key_display,
    get_genshin_window_info,
    is_admin,
)

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

SPEED_MODES = [
    ("🐢 An toàn", "safe"),
    ("⚡ Nhanh", "fast"),
    ("🚀 Siêu tốc", "turbo"),
    ("💥 Cực hạn", "extreme"),
]

TRIGGER_MODES = [
    ("💬 Khi có thoại", "dialogue"),
    ("⚡ Luôn spam trong Game", "always"),
]


class AutoSkipGUI(ctk.CTk):
    """Giao diện đồ họa nhỏ gọn (Mini Widget) hỗ trợ toàn diện Genshin Impact."""

    def __init__(self):
        super().__init__()

        # Nạp cấu hình
        self.config = Config()
        self.engine = AutoSkipEngine(self.config)

        # Trạng thái đang lắng nghe gán phím tắt (None, "start", "pause")
        self.recording_target: Optional[str] = None
        self._closing = False

        # Hàng đợi giao tiếp thread-safe giữa Engine và GUI
        self.event_queue: queue.Queue = queue.Queue()

        # Cài đặt cửa sổ chính mini
        self.title("Genshin Auto-Skip Turbo")
        self.geometry("420x560")
        self.minsize(390, 520)
        self.configure(fg_color="#0f172a")  # Slate 900 background

        # Áp dụng ghim cửa sổ theo config
        self.wm_attributes("-topmost", self.config.always_on_top)

        # Kết nối callback của Engine tới Queue
        self.engine.on_status_change = lambda status: self.event_queue.put(("status", status))
        self.engine.on_log = lambda msg, cat: self.event_queue.put(("log", (msg, cat)))
        self.engine.on_stats_update = lambda s, c, cps: self.event_queue.put(("stats", (s, c, cps)))
        self.engine.on_window_check = (
            lambda act, title, w, h, win_mode, ox, oy: self.event_queue.put(
                ("window", (act, title, w, h, win_mode, ox, oy))
            )
        )
        self.engine.on_hotkey_recorded = (
            lambda target, key_name: self.event_queue.put(
                ("hotkey_recorded", (target, key_name))
            )
        )

        # Bắt sự kiện phím trong Tkinter để chặn hành vi click mặc định khi đang gán phím
        self.bind("<KeyPress>", self._on_tk_key_press)

        # Xây dựng các thành phần giao diện gọn gàng
        self._build_ui()

        # Thông báo khởi động ngắn gọn
        start_disp = format_key_display(self.config.hotkey_start)
        self._append_log(f"Đã sẵn sàng. Bấm [{start_disp}] để bắt đầu tua thoại.", "info")
        for warning in self.config.warnings:
            self._append_log(warning, 'warning')

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

        # 2. NÚT ĐIỀU KHIỂN CHÍNH & GÁN PHÍM TẮT (CONTROLS & KEYBINDS)
        self._build_controls()

        # 3. CÀI ĐẶT CHẾ ĐỘ SPAM & TỐC ĐỘ (MODES & SPEED)
        self._build_modes_card()

        # 4. CÀI ĐẶT ĐỘ PHÂN GIẢI & TIỆN ÍCH (SETTINGS)
        self._build_settings_card()

        # 5. HỘP THÔNG BÁO HỆ THỐNG (LOG MINI)
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
        row1.pack(fill="x", padx=10, pady=(6, 2))

        pause_disp = format_key_display(self.config.hotkey_pause)
        self.status_indicator = ctk.CTkLabel(
            row1,
            text=f"⏸️ TẠM DỪNG ({pause_disp})",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color="#f59e0b"
        )
        self.status_indicator.pack(side="left")

        # Admin status badge
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

        # Dòng 3: Thống kê Tua & Chọn & Tốc độ thực tế CPS
        stats_frame = ctk.CTkFrame(self.status_card, fg_color="#0f172a", corner_radius=6)
        stats_frame.pack(fill="x", padx=8, pady=(0, 6))

        self.skip_counter_label = ctk.CTkLabel(
            stats_frame,
            text="⏩ Tua: 0",
            font=ctk.CTkFont(size=10, weight="bold"),
            text_color="#38bdf8"
        )
        self.skip_counter_label.pack(side="left", expand=True, pady=3)

        sep = ctk.CTkFrame(stats_frame, width=1, height=12, fg_color="#334155")
        sep.pack(side="left", pady=2)

        self.choice_counter_label = ctk.CTkLabel(
            stats_frame,
            text="🎯 Chọn: 0",
            font=ctk.CTkFont(size=10, weight="bold"),
            text_color="#fbbf24"
        )
        self.choice_counter_label.pack(side="left", expand=True, pady=3)

        sep2 = ctk.CTkFrame(stats_frame, width=1, height=12, fg_color="#334155")
        sep2.pack(side="left", pady=2)

        self.cps_counter_label = ctk.CTkLabel(
            stats_frame,
            text="⚡ 0/s",
            font=ctk.CTkFont(size=10, weight="bold"),
            text_color="#ec4899"
        )
        self.cps_counter_label.pack(side="left", expand=True, pady=3)

        sep3 = ctk.CTkFrame(stats_frame, width=1, height=12, fg_color="#334155")
        sep3.pack(side="left", pady=2)

        self.res_badge = ctk.CTkLabel(
            stats_frame,
            text=f"📐 {self.config.width}x{self.config.height}",
            font=ctk.CTkFont(size=10, weight="bold"),
            text_color="#93c5fd"
        )
        self.res_badge.pack(side="left", expand=True, pady=3)

    def _build_controls(self):
        ctrl_frame = ctk.CTkFrame(self.main_container, fg_color="transparent")
        ctrl_frame.pack(fill="x", pady=(0, 6))

        # Dòng 1: Hai nút lớn thao tác chính ▶ BẮT ĐẦU và ⏸ TẠM DỪNG
        btn_row = ctk.CTkFrame(ctrl_frame, fg_color="transparent")
        btn_row.pack(fill="x")

        start_disp = format_key_display(self.config.hotkey_start)
        pause_disp = format_key_display(self.config.hotkey_pause)

        self.btn_start = ctk.CTkButton(
            btn_row,
            text=f"▶ BẮT ĐẦU ({start_disp})",
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color="#16a34a",
            hover_color="#15803d",
            height=32,
            corner_radius=6,
            command=self._on_start_click
        )
        self.btn_start.pack(side="left", fill="x", expand=True, padx=(0, 3))

        self.btn_pause = ctk.CTkButton(
            btn_row,
            text=f"⏸ TẠM DỪNG ({pause_disp})",
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color="#d97706",
            hover_color="#b45309",
            height=32,
            corner_radius=6,
            command=self._on_pause_click
        )
        self.btn_pause.pack(side="left", fill="x", expand=True, padx=(3, 0))

        # Dòng 2: Nút bấm để gán phím tắt tùy ý (Bấm vào -> Nhấn phím bất kỳ để gán)
        bind_row = ctk.CTkFrame(ctrl_frame, fg_color="transparent")
        bind_row.pack(fill="x", pady=(4, 0))

        self.btn_bind_start = ctk.CTkButton(
            bind_row,
            text=f"⌨ Đổi phím: {start_disp}",
            font=ctk.CTkFont(size=10, weight="bold"),
            fg_color="#1e293b",
            hover_color="#334155",
            border_width=1,
            border_color="#475569",
            height=24,
            corner_radius=5,
            command=self._on_bind_start_click
        )
        self.btn_bind_start.pack(side="left", fill="x", expand=True, padx=(0, 3))

        self.btn_bind_pause = ctk.CTkButton(
            bind_row,
            text=f"⌨ Đổi phím: {pause_disp}",
            font=ctk.CTkFont(size=10, weight="bold"),
            fg_color="#1e293b",
            hover_color="#334155",
            border_width=1,
            border_color="#475569",
            height=24,
            corner_radius=5,
            command=self._on_bind_pause_click
        )
        self.btn_bind_pause.pack(side="left", fill="x", expand=True, padx=(3, 3))

        self.btn_reset_keys = ctk.CTkButton(
            bind_row,
            text="↺",
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color="#1e293b",
            hover_color="#334155",
            border_width=1,
            border_color="#475569",
            width=28,
            height=24,
            corner_radius=5,
            command=self._on_reset_keys_click
        )
        self.btn_reset_keys.pack(side="right")

    def _build_modes_card(self):
        """Card chọn chế độ tốc độ spam và chế độ kích hoạt."""
        modes_card = ctk.CTkFrame(
            self.main_container,
            fg_color="#1e293b",
            corner_radius=10,
            border_width=1,
            border_color="#334155"
        )
        modes_card.pack(fill="x", pady=(0, 6))

        # Tiêu đề Card
        title_row = ctk.CTkFrame(modes_card, fg_color="transparent")
        title_row.pack(fill="x", padx=8, pady=(4, 2))
        ctk.CTkLabel(
            title_row,
            text="⚡ Cài Đặt Chế Độ & Tốc Độ Spam",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color="#38bdf8"
        ).pack(side="left")

        # 1. Chọn tốc độ spam (Segmented Button)
        speed_row = ctk.CTkFrame(modes_card, fg_color="transparent")
        speed_row.pack(fill="x", padx=8, pady=(2, 4))

        speed_labels = [label for label, _ in SPEED_MODES]
        self.seg_speed = ctk.CTkSegmentedButton(
            speed_row,
            values=speed_labels,
            font=ctk.CTkFont(size=10, weight="bold"),
            height=26,
            command=self._on_speed_change,
            selected_color="#2563eb",
            selected_hover_color="#1d4ed8"
        )
        current_speed_label = speed_labels[2]  # Default turbo
        for label, val in SPEED_MODES:
            if val == self.config.spam_mode:
                current_speed_label = label
                break
        self.seg_speed.set(current_speed_label)
        self.seg_speed.pack(fill="x")

        # 2. Chọn chế độ kích hoạt: Khi có thoại vs Luôn spam
        trigger_row = ctk.CTkFrame(modes_card, fg_color="transparent")
        trigger_row.pack(fill="x", padx=8, pady=(2, 4))

        trigger_labels = [label for label, _ in TRIGGER_MODES]
        self.seg_trigger = ctk.CTkSegmentedButton(
            trigger_row,
            values=trigger_labels,
            font=ctk.CTkFont(size=10, weight="bold"),
            height=26,
            command=self._on_trigger_change,
            selected_color="#059669",
            selected_hover_color="#047857"
        )
        current_trigger_label = trigger_labels[0]
        for label, val in TRIGGER_MODES:
            if val == self.config.trigger_mode:
                current_trigger_label = label
                break
        self.seg_trigger.set(current_trigger_label)
        self.seg_trigger.pack(fill="x")

        # 3. Phím bấm + Nhịp spam (Burst) + Combo chuột trái
        opts_row = ctk.CTkFrame(modes_card, fg_color="transparent")
        opts_row.pack(fill="x", padx=8, pady=(2, 6))

        ctk.CTkLabel(opts_row, text="Phím:", font=ctk.CTkFont(size=10)).pack(side="left")
        self.key_combo = ctk.CTkComboBox(
            opts_row,
            values=["F", "Space", "E", "Enter"],
            width=60,
            height=24,
            font=ctk.CTkFont(size=10),
            command=self._on_key_change
        )
        self.key_combo.set(self.config.confirm_button.upper())
        self.key_combo.pack(side="left", padx=(2, 6))

        ctk.CTkLabel(opts_row, text="Nhịp:", font=ctk.CTkFont(size=10)).pack(side="left")
        self.burst_combo = ctk.CTkComboBox(
            opts_row,
            values=["1x", "2x", "3x", "5x"],
            width=55,
            height=24,
            font=ctk.CTkFont(size=10),
            command=self._on_burst_change
        )
        self.burst_combo.set(f"{self.config.burst_count}x")
        self.burst_combo.pack(side="left", padx=(2, 6))

        self.switch_click_combo = ctk.CTkSwitch(
            opts_row,
            text="+ Chuột Trái",
            font=ctk.CTkFont(size=10),
            command=self._on_click_combo_toggle
        )
        if self.config.click_combo:
            self.switch_click_combo.select()
        else:
            self.switch_click_combo.deselect()
        self.switch_click_combo.pack(side="right")

    def _build_settings_card(self):
        settings_card = ctk.CTkFrame(
            self.main_container,
            fg_color="#1e293b",
            corner_radius=10,
            border_width=1,
            border_color="#334155"
        )
        settings_card.pack(fill="x", pady=(0, 6))

        # Dòng 1: Dropdown màn hình + Nút Quét Game
        row1 = ctk.CTkFrame(settings_card, fg_color="transparent")
        row1.pack(fill="x", padx=8, pady=(4, 4))

        self.res_combo = ctk.CTkComboBox(
            row1,
            values=RESOLUTION_PRESETS,
            width=190,
            height=24,
            font=ctk.CTkFont(size=10),
            command=self._on_res_preset_change
        )
        self._init_res_combo_selection()
        self.res_combo.pack(side="left", fill="x", expand=True, padx=(0, 6))

        btn_scan = ctk.CTkButton(
            row1,
            text="🔍 Quét Game",
            font=ctk.CTkFont(size=10, weight="bold"),
            width=80,
            height=24,
            fg_color="#2563eb",
            hover_color="#1d4ed8",
            command=self._on_scan_game
        )
        btn_scan.pack(side="right")

        # Dòng 2: Ghim trên cùng
        row2 = ctk.CTkFrame(settings_card, fg_color="transparent")
        row2.pack(fill="x", padx=8, pady=(0, 4))

        self.switch_topmost = ctk.CTkSwitch(
            row2,
            text="Ghim cửa sổ trên cùng",
            font=ctk.CTkFont(size=10),
            command=self._on_topmost_toggle
        )
        if self.config.always_on_top:
            self.switch_topmost.select()
        else:
            self.switch_topmost.deselect()
        self.switch_topmost.pack(side="left")

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
            font=ctk.CTkFont(size=10, weight="bold"),
            text_color="#e2e8f0"
        ).pack(side="left")

        btn_clear = ctk.CTkButton(
            log_header,
            text="Xóa",
            font=ctk.CTkFont(size=9),
            width=36,
            height=18,
            fg_color="#334155",
            hover_color="#475569",
            command=self._clear_logs
        )
        btn_clear.pack(side="right")

        btn_reset_stats = ctk.CTkButton(
            log_header,
            text="Reset",
            font=ctk.CTkFont(size=9),
            width=42,
            height=18,
            fg_color="#334155",
            hover_color="#475569",
            command=self._reset_counters
        )
        btn_reset_stats.pack(side="right", padx=(0, 4))

        self.log_text = ctk.CTkTextbox(
            log_card,
            fg_color="#090d16",
            text_color="#cbd5e1",
            font=ctk.CTkFont(family="Consolas", size=9),
            corner_radius=6,
            border_width=1,
            border_color="#1e293b",
            height=70
        )
        self.log_text.pack(fill="both", expand=True, padx=8, pady=(0, 6))
        self.log_text.configure(state="disabled")

    # ========================== XỬ LÝ SỰ KIỆN ==========================
    def _process_events(self):
        """Đọc và xử lý các sự kiện từ Engine gửi qua queue (thread-safe)."""
        if self._closing:
            return
        try:
            while not self.event_queue.empty():
                event_type, payload = self.event_queue.get_nowait()
                if event_type == "status":
                    if payload == 'stopped':
                        self._on_close()
                        return
                    self._update_status_ui(payload)
                elif event_type == "log":
                    msg, cat = payload
                    self._append_log(msg, cat)
                elif event_type == "stats":
                    skips, choices, cps = payload
                    self._update_stats_ui(skips, choices, cps)
                elif event_type == "window":
                    act, title, cur_w, cur_h, is_win, ox, oy = payload
                    self._update_window_ui(act, title, cur_w, cur_h, is_win, ox, oy)
                elif event_type == "hotkey_recorded":
                    target, key_name = payload
                    self._handle_hotkey_recorded(target, key_name)
        except Exception as e:
            print(f"Lỗi xử lý hàng đợi sự kiện: {e}")

        self.after(50, self._process_events)

    def _update_status_ui(self, status: str):
        start_disp = format_key_display(self.config.hotkey_start)
        pause_disp = format_key_display(self.config.hotkey_pause)

        if status == "running":
            self.status_card.configure(border_color="#10b981", fg_color="#064e3b")
            self.status_indicator.configure(text=f"🟢 ĐANG CHẠY ({start_disp})", text_color="#34d399")
        elif status == "paused":
            self.status_card.configure(border_color="#f59e0b", fg_color="#1e293b")
            self.status_indicator.configure(text=f"⏸️ TẠM DỪNG ({pause_disp})", text_color="#f59e0b")
        elif status == "stopped":
            self.status_card.configure(border_color="#64748b", fg_color="#1e293b")
            self.status_indicator.configure(text="⚪ ĐÃ DỪNG", text_color="#94a3b8")

    def _update_stats_ui(self, skips: int, choices: int, cps: float = 0.0):
        self.skip_counter_label.configure(text=f"⏩ Tua: {skips}")
        self.choice_counter_label.configure(text=f"🎯 Chọn: {choices}")
        self.cps_counter_label.configure(text=f"⚡ {cps}/s")

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
            "key": "⌨️",
        }
        icon = icons.get(category, "•")
        time_str = datetime.datetime.now().strftime("%H:%M:%S")
        formatted_entry = f"[{time_str}] {icon} {msg}\n"

        self.log_text.configure(state="normal")
        self.log_text.insert("end", formatted_entry)

        # Giới hạn tối đa 30 dòng gần nhất để giữ app siêu nhẹ
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
        self._update_stats_ui(0, 0, 0.0)
        self._append_log("Đã đặt lại bộ đếm tua thoại và câu hỏi.", "info")

    # ========================== GÁN PHÍM TẮT TÙY CHỌN ==========================
    def _on_bind_start_click(self):
        if self.recording_target == "start":
            self._cancel_key_binding()
            return

        self.engine.pause()
        self.recording_target = "start"
        self.engine.recording_hotkey_for = "start"
        self.btn_bind_start.configure(
            text="🔴 Bấm phím / chuột...",
            fg_color="#b91c1c",
            hover_color="#991b1b"
        )
        pause_disp = format_key_display(self.config.hotkey_pause)
        self.btn_bind_pause.configure(
            text=f"⌨ Đổi phím: {pause_disp}",
            fg_color="#1e293b",
            hover_color="#334155"
        )
        self._append_log("Đang chờ phím cho [BẮT ĐẦU]... Bấm 1 phím hoặc nút chuột hông (Mouse 4/5) để gán (Esc để hủy).", "key")

    def _on_bind_pause_click(self):
        if self.recording_target == "pause":
            self._cancel_key_binding()
            return

        self.engine.pause()
        self.recording_target = "pause"
        self.engine.recording_hotkey_for = "pause"
        self.btn_bind_pause.configure(
            text="🔴 Bấm phím / chuột...",
            fg_color="#b91c1c",
            hover_color="#991b1b"
        )
        start_disp = format_key_display(self.config.hotkey_start)
        self.btn_bind_start.configure(
            text=f"⌨ Đổi phím: {start_disp}",
            fg_color="#1e293b",
            hover_color="#334155"
        )
        self._append_log("Đang chờ phím cho [TẠM DỪNG]... Bấm 1 phím hoặc nút chuột hông (Mouse 4/5) để gán (Esc để hủy).", "key")

    def _cancel_key_binding(self):
        self.recording_target = None
        self.engine.recording_hotkey_for = None
        self._refresh_hotkey_buttons()
        self._append_log("Đã hủy thay đổi phím tắt.", "info")

    def _on_reset_keys_click(self):
        self.recording_target = None
        self.engine.recording_hotkey_for = None
        if not self._save_config(hotkey_start="f8", hotkey_pause="f9"):
            return
        self._refresh_hotkey_buttons()
        self._update_status_ui(self.engine.status)
        self._append_log("Đã khôi phục phím tắt mặc định: [F8] Bắt đầu | [F9] Tạm dừng.", "success")

    def _refresh_hotkey_buttons(self):
        start_disp = format_key_display(self.config.hotkey_start)
        pause_disp = format_key_display(self.config.hotkey_pause)

        self.btn_start.configure(text=f"▶ BẮT ĐẦU ({start_disp})")
        self.btn_pause.configure(text=f"⏸ TẠM DỪNG ({pause_disp})")

        self.btn_bind_start.configure(
            text=f"⌨ Đổi phím: {start_disp}",
            fg_color="#1e293b",
            hover_color="#334155"
        )
        self.btn_bind_pause.configure(
            text=f"⌨ Đổi phím: {pause_disp}",
            fg_color="#1e293b",
            hover_color="#334155"
        )

    def _handle_hotkey_recorded(self, target: str, key_name: str):
        self.recording_target = None
        self._refresh_hotkey_buttons()
        self._update_status_ui(self.engine.status)

        if key_name == "cancelled":
            self._append_log("Đã hủy thay đổi phím tắt.", "info")
            return

        if key_name.startswith('error:'):
            self._append_log(key_name.split(':', 1)[1], 'warning')
            return

        disp_details = {
            "mouse4": "Mouse 4 (Chuột hông 1)",
            "mouse5": "Mouse 5 (Chuột hông 2)",
            "mouse3": "Mouse 3 (Chuột giữa)",
        }
        disp = disp_details.get(key_name, format_key_display(key_name))
        action_name = "BẮT ĐẦU" if target == "start" else "TẠM DỪNG"
        self._append_log(f"Đã gán phím tắt [{action_name}] thành: [{disp}]", "success")

    def _on_tk_key_press(self, event):
        # Nếu đang trong chế độ gán phím, chặn các phím Space/Enter của Tkinter kích hoạt widget
        if self.recording_target:
            return "break"

    # ========================== CALLBACKS NGƯỜI DÙNG ==========================
    def _save_config(self, **changes) -> bool:
        try:
            self.config.save(**changes)
        except (ValueError, OSError) as exc:
            self._append_log(f'Không thể lưu thiết lập: {exc}', 'warning')
            return False
        return True

    def _on_start_click(self):
        self.engine.start()

    def _on_pause_click(self):
        self.engine.pause()

    def _on_speed_change(self, selected_label: str):
        mode_val = "turbo"
        for label, val in SPEED_MODES:
            if label == selected_label:
                mode_val = val
                break
        if not self._save_config(spam_mode=mode_val):
            self.seg_speed.set(next(label for label, value in SPEED_MODES if value == self.config.spam_mode))
            return
        desc = {
            "safe": "Mô phỏng người thật, an toàn (~5 lần/giây)",
            "fast": "Nhanh, đều đặn (~15-20 lần/giây)",
            "turbo": "Siêu tốc, tua thoại xé gió (~40-60 lần/giây)",
            "extreme": "Cực hạn, tốc độ tối đa (~100+ lần/giây)"
        }.get(mode_val, "")
        self._append_log(f"Đã chọn: [{selected_label}] - {desc}", "success")

    def _on_trigger_change(self, selected_label: str):
        trigger_val = "dialogue"
        for label, val in TRIGGER_MODES:
            if label == selected_label:
                trigger_val = val
                break
        if not self._save_config(trigger_mode=trigger_val):
            self.seg_trigger.set(next(label for label, value in TRIGGER_MODES if value == self.config.trigger_mode))
            return
        desc = "Chỉ khi phát hiện hội thoại" if trigger_val == "dialogue" else "Luôn spam khi vào game (Loot đồ & Skip thoại)"
        self._append_log(f"Chế độ: [{desc}]", "info")

    def _on_key_change(self, value: str):
        btn = value.strip().lower()
        if not self._save_config(confirm_button=btn):
            self.key_combo.set(self.config.confirm_button.upper())
            return
        self.key_combo.set(self.config.confirm_button.upper())
        self._append_log(f"Đã đổi phím tương tác: [{btn.upper()}]", "info")

    def _on_burst_change(self, value: str):
        try:
            num = int(value.replace("x", "").strip())
        except ValueError:
            self._append_log('Nhịp spam phải là số nguyên trong khoảng 1–5.', 'warning')
        else:
            if self._save_config(burst_count=num):
                self._append_log(f"Đã đặt nhịp spam: {num} lần / đợt", "info")
        self.burst_combo.set(f'{self.config.burst_count}x')

    def _on_click_combo_toggle(self):
        is_on = bool(self.switch_click_combo.get())
        if not self._save_config(click_combo=is_on):
            (self.switch_click_combo.select if self.config.click_combo else self.switch_click_combo.deselect)()
            return
        msg = "Đã bật: Kèm Click chuột trái (Tua & chọn siêu tốc)" if is_on else "Đã tắt: Kèm Click chuột trái"
        self._append_log(msg, "info")

    def _on_res_preset_change(self, selected: str):
        if "Tự động" in selected:
            if not self._save_config(auto_window_mode=True, resolution_preset="auto"):
                self._init_res_combo_selection()
                return
            self._append_log("Đã bật: Tự động theo cửa sổ game", "success")
            return

        match = re.search(r"(\d+)[\xd7x](\d+)", selected)
        if match:
            w = int(match.group(1))
            h = int(match.group(2))
            if not self._save_config(width=w, height=h, auto_window_mode=False, resolution_preset=selected):
                self._init_res_combo_selection()
                return
            self.res_badge.configure(text=f"📐 {w}x{h}")
            self._append_log(f"Đã chọn độ phân giải: {w}x{h}", "info")

    def _on_scan_game(self):
        """Quét và tìm kiếm cửa sổ Genshin Impact thực tế."""
        is_fg, hwnd, title, client_x, client_y, client_w, client_h, is_windowed = get_genshin_window_info()
        if hwnd and client_w > 100 and client_h > 100:
            mode = "Cửa Sổ" if is_windowed else "Toàn Màn Hình"
            pos = f" tại ({client_x}, {client_y})" if is_windowed else ""
            if not self._save_config(width=client_w, height=client_h):
                return
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
            if not self._save_config(width=w, height=h):
                return
            self.res_badge.configure(text=f"📐 {w}x{h}")
            self._append_log(f"Chưa mở game. Đã nhận diện màn hình: {w}x{h}", "info")

    def _on_topmost_toggle(self):
        is_top = bool(self.switch_topmost.get())
        if not self._save_config(always_on_top=is_top):
            (self.switch_topmost.select if self.config.always_on_top else self.switch_topmost.deselect)()
            return
        self.wm_attributes("-topmost", is_top)
        msg = "Đã ghim cửa sổ trên cùng" if is_top else "Đã bỏ ghim cửa sổ"
        self._append_log(msg, "info")

    def _on_close(self):
        if self._closing:
            return
        self._closing = True
        self.engine.stop()
        self.destroy()


def main():
    app = AutoSkipGUI()
    app.mainloop()


if __name__ == "__main__":
    main()
