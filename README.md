# Genshin Impact - Tự Động Bỏ Qua Hội Thoại (Dialogue Auto-Skip)

> **⚠️ TUYÊN BỐ MIỄN TRỪ TRÁCH NHIỆM**: Việc sử dụng bất kỳ phần mềm bên thứ ba nào tác động hoặc tự động hóa trong Genshin Impact đều có thể vi phạm Điều khoản dịch vụ (Terms of Service) của game. Bạn tự chịu mọi rủi ro khi sử dụng công cụ này. Tác giả script không chịu trách nhiệm đối với bất kỳ hậu quả nào, bao gồm khả năng bị khóa tài khoản.

---

## 📋 Mục lục

- [Tổng quan & Tác dụng](#-tổng-quan--tác-dụng)
- [Giao diện Trực quan (GUI)](#-giao-diện-trực-quan-gui)
- [Các tính năng nổi bật](#-các-tính-năng-nổi-bật)
- [Yêu cầu hệ thống](#-yêu-cầu-hệ-thống)
- [Cài đặt](#-cài-đặt)
    - [Cách 1: Khởi chạy 1 chạm (Khuyến nghị)](#cách-1-khởi-chạy-1-chạm-khuyến-nghị)
    - [Cách 2: Chạy thủ công](#cách-2-chạy-thủ-công)
- [Hướng dẫn sử dụng](#-hướng-dẫn-sử-dụng)
- [Các phím tắt điều khiển](#-các-phím-tắt-điều-khiển)
- [Cấu hình hệ thống (.env)](#-cấu-hình-hệ-thống-env)
- [Cơ chế hoạt động](#-cơ-chế-hoạt-động)
- [Khắc phục lỗi thường gặp (Troubleshooting)](#-khắc-phục-lỗi-thường-gặp)

---

## 🎮 Tổng quan & Tác dụng

**Genshin Impact Dialogue Auto-Skip** là một công cụ tự động tua và bỏ qua các đoạn hội thoại dài dòng trong Genshin Impact. Công cụ hoạt động thông qua việc:

- Tự động nhận diện thời điểm hội thoại đang diễn ra trên màn hình bằng cách phân tích màu sắc điểm ảnh (pixel detection).
- Tự động bấm liên tục phím tương tác (mặc định là phím **F**) để tua nhanh lời thoại qua từng câu.
- Khi xuất hiện bảng câu hỏi hoặc tùy chọn hội thoại, tool tự động chọn tùy chọn ở dưới cùng.
- Giả lập hành vi bấm phím ngẫu nhiên của con người và có các khoảng tạm nghỉ ngắn để an toàn.

---

## 🖥️ Giao diện Trực quan (GUI)

Phiên bản mới trang bị giao diện đồ họa hiện đại (**Dark Mode** theo phong cách Gaming/Slate), giúp bạn dễ dàng theo dõi và điều khiển mà không cần nhìn vào dòng lệnh đen trắng:

- **🟢 Thẻ Trạng Thái Sống (Hero Status)**:
  - Hiển thị trực quan trạng thái: `🟢 ĐANG CHẠY` / `⏸️ TẠM DỪNG` / `⚪ ĐÃ DỪNG`.
  - Giám sát thời gian thực cửa sổ game: Phát hiện chính xác khi nào bạn đang ở trong Genshin Impact.
  - Bộ đếm thời gian thực: Thống kê số lần tua thoại (`⏩`) và số lần chọn đáp án (`🎯`).
- **🕹️ Phím Bấm Điều Khiển To Rõ**:
  - Nút lớn `▶ BẮT ĐẦU (F8)` và `⏸ TẠM DỪNG (F9)`.
  - Phím tắt toàn cục vẫn hoạt động song song mượt mà ngay cả khi đang thu nhỏ app.
- **⚙️ Bảng Cài Đặt Nhanh**:
  - Chọn phím bấm tương tác ngay trên menu (`F`, `Space`, `E`, `Enter`).
  - **Hỗ trợ đầy đủ mọi chế độ hiển thị Genshin Impact**:
    - **Cửa Sổ (Windowed)**: `1680×1050` (16:10), `1440×1080` (4:3), `1440×900`, `1366×768`, `1280×1024`, `1280×800`, `1280×720`, `1176×664`...
    - **Toàn Màn Hình / Không Viền (Borderless / Fullscreen)**: `1920×1080`, 2K `2560×1440`, 4K `3840×2160`, UltraWide `2560×1080`, `3440×1440`.
  - Nút `🔍 Quét Game`: Tự động tìm cửa sổ game, đo kích thước và vị trí (X, Y) chính xác trên màn hình.
  - Tự động bám theo cửa sổ game: Dù bạn di chuyển cửa sổ Genshin đi đâu, tool tự động bám tọa độ vào trong game.
  - Công tắc `Ghim trên cùng (Always on top)`: Giữ cửa sổ tool luôn nổi trên game.
  - Công tắc `Mô phỏng người thật`: Bật/tắt ngẫu nhiên hóa độ trễ và nghỉ ngơi ngẫu nhiên.
- **📋 Thông Báo Hệ Thống**:
  - Chỉ ghi lại các thông báo quan trọng, ngắn gọn, không spam log từng lần click phím.
  - Nút Xóa nhật ký và Reset bộ đếm thống kê.

---

## ✨ Các tính năng nổi bật

- **Giao diện người dùng trực quan**: Đầy đủ đồ họa, không cần sửa file cấu hình thủ công.
- **Hỗ trợ hoàn hảo Chế độ Cửa Sổ (Windowed Mode)**: Tự động tính tọa độ từ góc client của game, dù cửa sổ ở bất kỳ vị trí nào trên màn hình.
- **Dò tìm đa điểm (Tolerance Patch Scan)**: Quét vùng lân cận ±3px quanh nút Auto và lựa chọn thoại, đảm bảo không bao giờ bị trượt pixel do co giãn màn hình.
- **Nhận diện hội thoại tự động**: Dùng pixel detection kiểm tra nút Auto-Play và biểu tượng thoại.
- **Tự động chọn đáp án**: Luôn chọn phương án đối thoại ở dòng dưới cùng.
- **Hỗ trợ đa độ phân giải**: Tự động nhận diện và tính toán tọa độ tương thích với nhiều độ phân giải màn hình (Full HD 1080p, 2K 1440p, 4K 2160p và màn hình UltraWide).
- **Mô phỏng hành vi người thật (Human-like)**:
    - Tần suất bấm ngẫu nhiên (dao động từ 0.12 đến 0.20 giây/lần).
    - Tự động tạm nghỉ ngẫu nhiên từ 3 đến 7 giây (mỗi 30 giây có tỉ lệ nghỉ).
- **An toàn & Thông minh**:
    - Chỉ kích hoạt khi cửa sổ game Genshin Impact đang là cửa sổ hoạt động chính (Active Window).
    - Tự động nhận diện và không thao tác khi đang ở màn hình tải (Loading Screen).
- **Khởi chạy 1 chạm**: File `run.bat` tự động kiểm tra môi trường, cài đặt thư viện và mở giao diện.
- **Hỗ trợ cả 2 chế độ**: Chạy mặc định qua GUI đẹp mắt, hoặc chạy chế độ dòng lệnh qua `run.bat cli`.

---

## 📦 Yêu cầu hệ thống

### Yêu cầu phần cứng & Hệ điều hành

- **Hệ điều hành**: Windows 10 / 11.
- **Màn hình**: Màn hình chính (Primary Display).
- **Quyền hạn**: Administrator (Cần quyền quản trị viên để gửi tín hiệu mô phỏng phím bấm vào game).

### Yêu cầu phần mềm

- **Python**: Phiên bản 3.11 trở lên (đã tích chọn "Add Python to PATH").
- **uv**: Trình quản lý gói Python (sẽ được tự động cài đặt qua file `run.bat`).
- Game **Genshin Impact** đang chạy trên máy.

### Thiết lập quan trọng trong game

> **BẮT BUỘC**: Mở menu game, vào **Cài đặt (Settings) > Khác (Other)** và chuyển mục **Tự Động Phát Cốt Truyện (Auto-Play Story)** thành **TẮT (Off)**.

---

## 🚀 Cài đặt

### Cách 1: Khởi chạy 1 chạm (Khuyến nghị)

1. Nhấp chuột phải vào file **`run.bat`** và chọn **"Run as administrator"** (Chạy với quyền quản trị viên).
2. File batch sẽ tự động:
    - Kiểm tra quyền Administrator.
    - Cài đặt/cập nhật trình quản lý gói `uv` và các thư viện cần thiết.
    - Tự động mở giao diện GUI của tool.

### Cách 2: Chạy thủ công

1. Cài đặt Python 3.11+ từ [python.org](https://www.python.org/downloads/).
2. Mở Command Prompt / PowerShell với quyền Administrator tại thư mục này.
3. Đồng bộ thư viện:
    ```bash
    uv sync
    ```
4. Khởi chạy giao diện GUI:
    ```bash
    uv run gui.py
    ```
    *(Hoặc chạy bản dòng lệnh: `uv run autoskip_dialogue.py`)*

---

## 📖 Hướng dẫn sử dụng

1. **Khởi động game Genshin Impact**.
2. **Chạy tool** bằng cách nhấp chuột phải vào `run.bat` chọn **Run as administrator**.
3. Cửa sổ giao diện trực quan sẽ hiện lên:
   - Tool tự động nhận diện độ phân giải màn hình của bạn.
   - Bạn có thể chỉnh lại phím tương tác trong ô cài đặt (mặc định là `F`).
4. **Bắt đầu tua hội thoại**:
   - Nhấn nút **▶ BẮT ĐẦU** trên giao diện, hoặc bấm phím tắt **F8**.
   - Chuyển sang cửa sổ Genshin Impact và tận hưởng: mọi câu thoại và lựa chọn sẽ được tự động bỏ qua cực nhanh!
   - Khi muốn tạm dừng, bấm **F9** hoặc nhấn **⏸ TẠM DỪNG**.

---

## ⌨️ Các phím tắt điều khiển

|  Phím   | Tác vụ               | Mô tả chi tiết                            |
| :-----: | :------------------- | :---------------------------------------- |
| **F8**  | **Bắt đầu (Start)**  | Kích hoạt chế độ tự động bỏ qua hội thoại |
| **F9**  | **Tạm dừng (Pause)** | Tạm thời ngưng tự động tua hội thoại      |
| **F12** | **Thoát (Exit)**     | Đóng và kết thúc chương trình hoàn toàn   |

---

## ⚙️ Cấu hình hệ thống (.env)

Tất cả cấu hình có thể điều chỉnh trực quan ngay trên GUI. Dữ liệu sẽ tự động đồng bộ vào file `.env`:

```env
WIDTH=1920
HEIGHT=1080
CONFIRM_BUTTON=f
DEVICE=mnk
ALWAYS_ON_TOP=true
HUMAN_SIMULATION=true
```

---

## 🔧 Cơ chế hoạt động

1. **Quét màu Pixel (Pixel Color Detection)**:
    - Tool giám sát màu sắc tại vị trí nút phát tự động (Auto-Play) góc trên bên trái màn hình.
    - Kiểm tra màu sắc tại vùng hiển thị lựa chọn hội thoại.
    - Kiểm tra màn hình tải (loading screen) để ngưng bấm phím khi game đang load bản đồ.
2. **Mô phỏng bấm phím**:
    - Sử dụng thư viện `pyautogui` để gửi tín hiệu nhấn phím `F`.
    - Khoảng cách giữa các lần nhấn phím được tạo ngẫu nhiên từ `0.12s - 0.20s` để tránh hành vi bất thường giống bot.
    - Cứ mỗi 30 giây, script có tỉ lệ tự động tạm dừng từ 3 đến 7 giây để giả lập người chơi đang nghỉ tay.

---

## 🐛 Khắc phục lỗi thường gặp

- **Tool không thể chạy hoặc báo lỗi quyền hạn**:
    - _Khắc phục_: Hãy chắc chắn rằng bạn nhấp chuột phải vào `run.bat` và chọn **Run as administrator**.
- **Hội thoại không được tự động bỏ qua**:
    - Hãy kiểm tra xem bạn đã bấm **F8** để kích hoạt chưa (giao diện hiển thị `🟢 ĐANG CHẠY`).
    - Kiểm tra xem cửa sổ Genshin Impact có đang được chọn (Active) hay không.
    - Kiểm tra trong game mục **Cài đặt > Khác > Tự Động Phát Cốt Truyện** đã chuyển thành **Tắt** chưa.
    - Đảm bảo game đang hiển thị trên màn hình chính (Primary Display) nếu dùng nhiều màn hình.
- **Bị sai độ phân giải**:
    - Nhấn nút **🔄 Quét màn hình** trên giao diện để tool tự đo lại độ phân giải chính xác.
