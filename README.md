# Genshin Impact - Tự Động Bỏ Qua Hội Thoại & Nhặt Đồ (Dialogue Auto-Skip & Turbo Loot)

> **⚠️ TUYÊN BỐ MIỄN TRỪ TRÁCH NHIỆM**: Việc sử dụng bất kỳ phần mềm bên thứ ba nào tác động hoặc tự động hóa trong Genshin Impact đều có thể vi phạm Điều khoản dịch vụ (Terms of Service) của game. Bạn tự chịu mọi rủi ro khi sử dụng công cụ này. Tác giả script không chịu trách nhiệm đối với bất kỳ hậu quả nào, bao gồm khả năng bị khóa tài khoản.

---

## 📋 Mục lục

- [Tổng quan & Điểm mới trong Phiên bản Turbo](#-tổng-quan--điểm-mới)
- [Giao diện Trực quan (GUI)](#-giao-diện-trực-quan-gui)
- [Các chế độ hoạt động & Tốc độ](#-các-chế-độ-hoạt-động--tốc-độ)
- [Các tính năng nổi bật](#-các-tính-năng-nổi-bật)
- [Yêu cầu hệ thống](#-yêu-cầu-hệ-thống)
- [Cài đặt & Khởi chạy](#-cài-đặt--khởi-chạy)
- [Các phím tắt điều khiển](#-các-phím-tắt-điều-khiển)
- [Cấu hình hệ thống (.env)](#-cấu-hình-hệ-thống-env)
- [Khắc phục lỗi thường gặp (Troubleshooting)](#-khắc-phục-lỗi-thường-gặp)

---

## 🎮 Tổng quan & Điểm mới

**Genshin Impact Dialogue Auto-Skip Turbo** là công cụ tự động hóa tua nhanh lời thoại và tự động nhặt vật phẩm trong Genshin Impact với tốc độ cực cao:

- 🚀 **Gửi phím qua Win32**: Dùng `keybd_event` / `mouse_event` với thời gian giữ phím ngắn. Tốc độ thực tế phụ thuộc máy, tốc độ nhận diện và game.
- 💥 **Spam nhiều lần liên hoàn (Burst Multi-Press)**: Cho phép gửi nhiều lần phím liên tục mỗi nhịp (1x, 2x, 3x, 5x), giúp đối thoại trôi qua trong chớp mắt.
- 📜 **Tự động vượt màn hình dẫn chuyện (Black Cutscene / Narrative Monologue)**: Tự động phát hiện màn hình dẫn chuyện chữ trắng nền đen với dòng *"Nhấn để tiếp tục"* và biểu tượng thoi vàng ◆, tự động click / Space chuyển cảnh mượt mà.
- 🛡️ **Bộ lọc chống đánh thường ngoài map (Anti-Normal Attack Spam)**: Phân tích bối cảnh nhiều điểm ảnh để giảm nhận diện nhầm mây, tuyết, cát sa mạc hay số sát thương. Đây là bộ lọc theo màu, vẫn cần kiểm tra với hình ảnh thực tế trong game.
- 🎛️ **Đa chế độ linh hoạt**: Người dùng có thể tùy chọn 4 chế độ tốc độ khác nhau và 2 cách thức kích hoạt tùy theo nhu cầu.
- 🖱️ **Tùy chọn Combo Chuột Trái**: Kết hợp phím tương tác và click để tua thoại. Với bảng đáp án, tool di chuyển tới đáp án thấp nhất nhận diện được rồi click một lần mỗi đợt, không gửi kèm burst phím F.
- 🧭 **Chế độ Luôn Spam (Loot & Skip)**: Vừa tự động nhặt đồ / mở rương / hái hoa quả khi chạy map, vừa tua sạch đối thoại khi gặp NPC.

---

## 🎛️ Các chế độ hoạt động & Tốc độ

Tool cung cấp các chế độ tùy chỉnh ngay trên giao diện:

### 1. Chế độ Tốc độ (Speed Modes)

| Chế độ | Biểu tượng | Tần suất ước tính | Đặc điểm | Phù hợp cho |
| :--- | :---: | :---: | :--- | :--- |
| **An toàn** | 🐢 | ~4 - 6 lần/giây | Độ trễ ngẫu nhiên 120-200ms, thỉnh thoảng tạm nghỉ 3-5s mô phỏng người thật. | Người chơi ưu tiên tính tự nhiên, an toàn tối đa. |
| **Nhanh** | ⚡ | ~15 - 20 lần/giây | Nhấn đều đặn, không nghỉ ngơi, nhanh hơn bản cũ 5 lần. | Tua thoại mượt mà hàng ngày. |
| **Siêu tốc (Turbo)** | 🚀 | ~40 - 60 lần/giây | Bấm liên tục, gửi chuỗi phím đa nhịp, đối thoại trôi vèo vèo. *(Khuyến nghị)* | Cày nhiệm vụ dài dòng, tua thoại siêu tốc. |
| **Cực hạn (Extreme)** | 💥 | ~100+ lần/giây | Tốc độ tối đa phần cứng, xé gió, không giới hạn độ trễ. | Bỏ qua toàn bộ hội thoại nhanh nhất lịch sử game. |

### 2. Cách thức Kích hoạt (Trigger Modes)

- **💬 Khi có thoại (Dialogue Only)**:
  - Tự động nhận diện pixel của nút Auto-Play hoặc biểu tượng thoại.
  - Chỉ khi nào trong game xuất hiện khung thoại hoặc bảng lựa chọn đáp án thì tool mới spam phím.
- **⚡ Luôn spam trong Game (Always / Loot & Skip)**:
  - Cứ khi nào cửa sổ Genshin Impact đang Active (bạn đang trong game), tool sẽ tự động spam phím đều đặn.
  - Tác dụng vượt trội:
    - Đi chạy map, săn quái: Tự động nhặt đồ rơi, khoáng thạch, hoa quả, mở rương ngay tức thì khi lướt qua.
    - Gặp NPC: Tự động tua sạch đối thoại ngay từ câu đầu tiên mà không cần chờ nút Auto-Play xuất hiện.
    - Tự động phát hiện màn hình tải trắng (Loading Screen) để tạm dừng an toàn.

### 3. Tùy chọn nâng cao

- **Nhịp spam (Burst Count)**: Chọn số lần nhấn phím mỗi đợt (`1x`, `2x`, `3x`, `5x`).
- Safe dùng 1 lần/đợt; Fast tối đa 2 lần/đợt. Turbo và Extreme dùng nhịp đã chọn, kể cả `1x`. Các tần suất ở bảng trên chỉ là ước tính, chưa phải benchmark.
- **+ Chuột Trái (Left Click Combo)**: Kết hợp Click chuột trái cùng với phím F để tua thoại thần tốc và tự động bấm chọn câu trả lời ở bảng thoại.

---

## 🖥️ Giao diện Trực quan (GUI)

- **🟢 Thẻ Trạng Thái Sống (Hero Status)**:
  - Trạng thái trực quan: `🟢 ĐANG CHẠY` / `⏸️ TẠM DỪNG` / `⚪ ĐÃ DỪNG`.
  - Giám sát cửa sổ game theo thời gian thực (đo đạc kích thước và tọa độ client).
  - Đồng hồ đo tốc độ thực tế: `⏩ Tua`, `🎯 Chọn`, và `⚡ CPS (Số lần click/giây)`.
- **🕹️ Phím Bấm Điều Khiển**: Nút lớn `▶ BẮT ĐẦU (F8)` và `⏸ TẠM DỪNG (F9)`.
- **⚡ Bảng Chọn Chế Độ 1 Chạm**: Segmented button trực quan chuyển đổi giữa 4 tốc độ và 2 cách kích hoạt.
- **⚙️ Thiết lập hiển thị**:
  - Hỗ trợ mọi tỷ lệ: 16:9, 16:10, 4:3, 5:4, UltraWide 21:9.
  - Tự động bám tọa độ chuẩn xác trong cả chế độ Cửa sổ (Windowed) và Toàn màn hình.
  - Nút `🔍 Quét Game` tự động dò cửa sổ Genshin đang mở.
  - Công tắc `Ghim cửa sổ trên cùng (Always on top)`.

---

## ⌨️ Các phím tắt điều khiển (Tùy chỉnh tự do)

Mặc định công cụ sử dụng:
| Phím mặc định | Tác vụ | Mô tả |
| :---: | :--- | :--- |
| **F8** | **Bắt đầu (Start)** | Kích hoạt tự động tua thoại / spam |
| **F9** | **Tạm dừng (Pause)** | Tạm ngưng hoạt động |
| **F12** | **Thoát (Exit)** | Đóng tool hoàn toàn |

> **💡 Tính năng Đổi phím 1 chạm (Hỗ trợ cả 2 Nút Chuột Hông)**:
> - Trên giao diện có 2 nút `⌨ Đổi phím: F8` và `⌨ Đổi phím: F9`.
> - Bạn chỉ cần nhấp vào nút đó (nút sẽ chuyển sang `🔴 Bấm phím / chuột...`), sau đó:
>   - **Bấm phím hợp lệ** trên bàn phím (F1-F11, phím chữ, phím số, Numpad...). Không dùng phím tương tác, Space, F12 hoặc phím đang gán cho tác vụ còn lại.
>   - **HOẶC bấm 2 nút chuột bên hông**: **Mouse 4** (Chuột hông 1) hoặc **Mouse 5** (Chuột hông 2), chuột giữa (**Mouse 3**)!
> - Tool sẽ nhận diện và gán ngay lập tức thành phím tắt mới.
> - Bấm `Esc` để hủy.
> - Tool tạm dừng khi bắt đầu đổi phím. F12 luôn đóng tool, kể cả khi đang đổi phím.
> - Bấm nút `↺` để khôi phục phím tắt mặc định (F8 / F9).
> - Phím tắt hoạt động toàn cục ngay cả khi đang thu nhỏ app hoặc đang trong game.

---

## 📦 Yêu cầu hệ thống

- **Hệ điều hành**: Windows 10 / 11.
- **Quyền hạn**: Administrator (Cần thiết để gửi tín hiệu bàn phím vào game).
- **Python**: Phiên bản 3.11 trở lên.
- **uv**: Trình quản lý gói siêu tốc (tự động cài đặt qua `run.bat`).

> **Lưu ý trong game**: Mở menu game, vào **Cài đặt (Settings) > Khác (Other)** và chuyển mục **Tự Động Phát Cốt Truyện (Auto-Play Story)** thành **TẮT (Off)**.

---

## 🚀 Cài đặt & Khởi chạy

### Cách 1: Khởi chạy 1 chạm (Khuyến nghị)
1. Nhấp chuột phải vào file **`run.bat`** và chọn **"Run as administrator"**.
2. File batch sẽ tự động cài đặt các thư viện cần thiết và mở giao diện GUI.

### Cách 2: Chạy dòng lệnh (CLI)
- Mở Terminal/CMD với quyền Admin tại thư mục tool:
  ```bash
  uv run gui.py
  ```
  *(Hoặc chạy bản console: `uv run autoskip_dialogue.py`)*

---

## ⚙️ Cấu hình hệ thống (.env)

Các thiết lập được tự động lưu lại vào file `.env` mỗi khi bạn thay đổi trên giao diện:

| Biến | Mặc định | Ý nghĩa |
| :--- | :---: | :--- |
| `HOTKEY_START` | `f8` | Phím tắt kích hoạt chạy (Bắt đầu) |
| `HOTKEY_PAUSE` | `f9` | Phím tắt tạm dừng |
| `SPAM_MODE` | `turbo` | Chế độ tốc độ: `safe`, `fast`, `turbo`, `extreme` |
| `TRIGGER_MODE` | `dialogue` | Cách kích hoạt: `dialogue` (khi có thoại), `always` (luôn spam) |
| `BURST_COUNT` | `2` | Số nguyên từ 1 đến 5; GUI có sẵn 1, 2, 3, 5 |
| `CLICK_COMBO` | `false` | Bật/tắt click chuột trái kèm theo: `true`/`false` |
| `CONFIRM_BUTTON`| `f` | Một phím `a`–`z`, `0`–`9`, `space` hoặc `enter` |
| `ALWAYS_ON_TOP`| `true` | Ghim cửa sổ tool luôn nổi trên game |
| `AUTO_WINDOW_MODE`| `true` | Tự động thích ứng kích thước cửa sổ game |

`WIDTH` và `HEIGHT`, nếu đặt thủ công, phải là số nguyên trong khoảng 1–16384.
Cấu hình nạp sai được thay bằng giá trị mặc định trong bộ nhớ và hiện cảnh báo.
Thay đổi không hợp lệ trên GUI bị từ chối; thiết lập đang dùng được giữ lại.
File cấu hình được lưu tại đường dẫn đã chọn khi khởi tạo, không đổi theo thư mục làm việc.

## Các sửa sau rà soát

- Nhận diện game qua executable `GenshinImpact.exe` / `YuanShen.exe`, không dựa vào tiêu đề trình duyệt. Nếu không truy vấn được tiến trình, tool không gửi thao tác.
- Kiểm tra lại cửa sổ hiện hành và trạng thái chạy trước từng lần nhấn/click. Phím và nút chuột luôn được nhả sau lần nhấn hiện tại.
- Không cho phím Start/Pause trùng nhau hoặc trùng phím tool tự gửi. Bỏ qua sự kiện bàn phím được phần mềm tạo ra khi xử lý hotkey.
- Giữ vị trí gốc của cửa sổ game khi chọn độ phân giải thủ công.
- F12 đóng cả GUI và engine; không còn hiển thị đang chạy sau khi worker đã dừng.
- Extreme tôn trọng nhịp `1x`; đáp án được click tại tọa độ nhận diện được.
- Kiểm tra cấu hình trước khi lưu; lỗi ghi file không làm đổi cấu hình đang chạy.
- Thêm test hồi quy, bỏ mã không dùng và ngừng theo dõi bytecode Python.

Việc kiểm tra focus và gửi input là hai lời gọi riêng; vẫn có một khoảng rất ngắn giữa chúng.
Độ chính xác nhận diện pixel và tốc độ thực tế cần được thử trực tiếp trong game.

## Kiểm thử

Chạy từ thư mục dự án trên Windows:

```powershell
.\.venv\Scripts\python.exe -B -m unittest discover -v
```

Hoặc: `uv run --frozen python -B -m unittest discover -v`.
Test dùng file cấu hình tạm và mô phỏng input/cửa sổ/pixel, không gửi phím/click thật hay bật hook toàn cục.
