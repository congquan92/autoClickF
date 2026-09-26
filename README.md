# Genshin Impact - Tự Động Bỏ Qua Hội Thoại (Dialogue Auto-Skip)

> **⚠️ TUYÊN BỐ MIỄN TRỪ TRÁCH NHIỆM**: Việc sử dụng bất kỳ phần mềm bên thứ ba nào tác động hoặc tự động hóa trong Genshin Impact đều có thể vi phạm Điều khoản dịch vụ (Terms of Service) của game. Bạn tự chịu mọi rủi ro khi sử dụng công cụ này. Tác giả script không chịu trách nhiệm đối với bất kỳ hậu quả nào, bao gồm khả năng bị khóa tài khoản.

---

## 📋 Mục lục

- [Tổng quan & Tác dụng](#-tổng-quan--tác-dụng)
- [Các tính năng nổi bật](#-các-tính-năng-nổi-bật)
- [Yêu cầu hệ thống](#-yêu-cầu-hệ-thống)
- [Cài đặt](#-cài-đặt)
    - [Cách 1: Cài đặt tự động (Khuyến nghị)](#cách-1-cài-đặt-tự-động-khuyến-nghị)
    - [Cách 2: Cài đặt thủ công](#cách-2-cài-đặt-thủ-công)
- [Hướng dẫn sử dụng](#-hướng-dẫn-sử-dụng)
- [Các phím tắt điều khiển](#-các-phím-tắt-điều-khiển)
- [Cấu hình hệ thống (.env)](#-cấu-hình-hệ-thống-env)
- [Cơ chế hoạt động](#-cơ-chế-hoạt-động)
- [Khắc phục lỗi thường gặp (Troubleshooting)](#-khắc-phục-lỗi-thường-gặp)

---

## 🎮 Tổng quan & Tác dụng

**Genshin Impact Dialogue Auto-Skip** là một công cụ tự động tua và bỏ qua các đoạn hội thoại dài dòng trong Genshin Impact. Công cụ này hoạt động thông qua việc:

- Tự động nhận diện thời điểm hội thoại đang diễn ra trên màn hình bằng cách phân tích màu sắc điểm ảnh (pixel detection).
- Tự động bấm liên tục phím tương tác (mặc định là phím **F**) để tua nhanh lời thoại qua từng câu.
- Khi xuất hiện các bảng câu hỏi hoặc tùy chọn lựa chọn hội thoại, tool sẽ tự động chọn tùy chọn ở dưới cùng.
- Giả lập hành vi bấm phím ngẫu nhiên của con người và có các khoảng tạm nghỉ ngắn để tránh bị cơ chế chống gian lận phát hiện.

---

## ✨ Các tính năng nổi bật

- **Nhận diện hội thoại tự động**: Sử dụng nhận diện pixel để biết chính xác khi nào đoạn hội thoại đang chạy.
- **Tự động chọn đáp án**: Luôn chọn phương án đối thoại ở dòng dưới cùng.
- **Hỗ trợ đa độ phân giải**: Tự động nhận diện và tính toán tọa độ tương thích với nhiều độ phân giải màn hình khác nhau (Full HD 1080p, 2K 1440p, 4K 2160p và màn hình siêu rộng UltraWide).
- **Mô phỏng hành vi người thật (Human-like)**:
    - Tần suất bấm phím ngẫu nhiên (dao động từ 0.12 đến 0.20 giây/lần).
    - Tự động tạm nghỉ ngẫu nhiên từ 3 đến 8 giây (tỉ lệ 4% mỗi 30 giây).
- **An toàn & Thông minh**:
    - Chỉ kích hoạt khi cửa sổ game Genshin Impact đang là cửa sổ hoạt động chính (Active Window).
    - Tự động nhận diện và không thao tác khi đang ở màn hình tải (Loading Screen).
- **Khởi chạy 1 chạm**: Tích hợp sẵn file `run.bat` tự động kiểm tra môi trường, cài đặt thư viện và chạy tool.

---

## 📦 Yêu cầu hệ thống

### Yêu cầu phần cứng & Hệ điều hành

- **Hệ điều hành**: Windows 10 / 11 (có hỗ trợ thư viện win32api).
- **Màn hình**: Màn hình chính (nếu dùng nhiều màn hình, hãy để cửa sổ game hiển thị trên màn hình chính - Primary Display).
- **Quyền hạn**: Administrator (Cần quyền quản trị viên để gửi tín hiệu mô phỏng phím bấm vào game).

### Yêu cầu phần mềm

- **Python**: Phiên bản 3.11 trở lên (đã tích chọn "Add Python to PATH").
- **uv**: Trình quản lý gói Python (sẽ được tự động cài đặt qua file `run.bat`).
- Game **Genshin Impact** đang chạy trên máy.

### Thiết lập quan trọng trong game

> **BẮT BUỘC**: Mở menu game, vào **Cài đặt (Settings) > Khác (Other)** và chuyển mục **Tự Động Phát Cốt Truyện (Auto-Play Story)** thành **TẮT (Off)**.

---

## 🚀 Cài đặt

### Cách 1: Cài đặt tự động (Khuyến nghị)

1. Nhấp chuột phải vào file **`run.bat`** trong thư mục dự án và chọn **"Run as administrator"** (Chạy với quyền quản trị viên).
2. File batch sẽ tự động:
    - Kiểm tra quyền Administrator.
    - Kiểm tra phiên bản Python trên máy.
    - Tự động cài đặt trình quản lý gói `uv` (nếu chưa có).
    - Tải và cài đặt tất cả các thư viện cần thiết.
    - Khởi động chương trình tự động.

### Cách 2: Cài đặt thủ công

1. Cài đặt Python 3.11+ từ [python.org](https://www.python.org/downloads/) (lưu ý tích chọn _Add Python to PATH_).
2. Mở Command Prompt / PowerShell với quyền Administrator tại thư mục này.
3. Cài đặt `uv`:
    ```bash
    pip install uv
    ```
4. Đồng bộ các thư viện:
    ```bash
    uv sync
    ```
5. Chạy tool:
    ```bash
    uv run autoskip_dialogue.py
    ```
6. Xoá các thư viện không cần thiết (nếu muốn):

    ```bash
    uv clean
    uv cache clean

    ```

---

## 📖 Hướng dẫn sử dụng

1. **Khởi động game Genshin Impact** và đảm bảo game đang chạy ở màn hình chính.
2. **Chạy tool** bằng cách nhấp chuột phải vào file `run.bat` chọn **Run as administrator**.
3. **Cấu hình lần đầu**:
    - Chương trình sẽ tự động đo độ phân giải màn hình của bạn.
    - Nhập phím tương tác trong game (thông thường là `F`, bạn chỉ cần nhấn Enter để chọn mặc định).
    - Thông tin sẽ tự động được lưu vào file `.env` cho các lần chạy sau.
4. **Kích hoạt Auto-Skip**:
    - Chuyển sang cửa sổ Genshin Impact.
    - Nhấn phím **F8** để bật tính năng tự động tua hội thoại.
    - Khi có hội thoại, tool sẽ tự động nhấn phím để tua qua câu thoại và tự chọn đáp án.

---

## ⌨️ Các phím tắt điều khiển

|  Phím   | Tác vụ               | Mô tả chi tiết                            |
| :-----: | :------------------- | :---------------------------------------- |
| **F8**  | **Bắt đầu (Start)**  | Kích hoạt chế độ tự động bỏ qua hội thoại |
| **F9**  | **Tạm dừng (Pause)** | Tạm thời ngưng tự động tua hội thoại      |
| **F12** | **Thoát (Exit)**     | Đóng và kết thúc chương trình hoàn toàn   |

---

## ⚙️ Cấu hình hệ thống (.env)

Sau lần chạy đầu tiên, chương trình sẽ tự động tạo hoặc cập nhật file `.env`:

```env
WIDTH=1920
HEIGHT=1080
CONFIRM_BUTTON=f
DEVICE=mnk
```

- **WIDTH**: Chiều rộng màn hình (tính bằng pixel, tự động nhận diện).
- **HEIGHT**: Chiều cao màn hình (tính bằng pixel, tự động nhận diện).
- **CONFIRM_BUTTON**: Phím bấm tương tác trong game (mặc định là `f`).
- **DEVICE**: Thiết bị đầu vào (`mnk` là bàn phím và chuột).

_Lưu ý_: Nếu màn hình của bạn nhận sai độ phân giải, bạn có thể mở trực tiếp file `.env` bằng Notepad để chỉnh sửa thủ công.

---

## 🔧 Cơ chế hoạt động

1. **Quét màu Pixel (Pixel Color Detection)**:
    - Tool giám sát màu sắc tại vị trí nút phát tự động (Auto-Play) góc trên bên trái màn hình.
    - Kiểm tra màu sắc tại vùng hiển thị lựa chọn hội thoại.
    - Kiểm tra màn hình tải (loading screen) để ngưng bấm phím khi game đang load bản đồ.
2. **Mô phỏng bấm phím**:
    - Sử dụng thư viện `pyautogui` để gửi tín hiệu nhấn phím `F`.
    - Khoảng cách giữa các lần nhấn phím được tạo ngẫu nhiên từ `0.12s - 0.20s` để tránh hành vi bất thường giống bot.
    - Cứ mỗi 30 giây, script có tỉ lệ 4% tự động tạm dừng từ 3 đến 8 giây để giả lập người chơi đang nghỉ tay.

---

## 🐛 Khắc phục lỗi thường gặp

- **Tool không thể chạy hoặc báo lỗi quyền hạn**:
    - _Khắc phục_: Hãy chắc chắn rằng bạn nhấp chuột phải vào `run.bat` và chọn **Run as administrator**.
- **Hội thoại không được tự động bỏ qua**:
    - Hãy kiểm tra xem bạn đã bấm **F8** để kích hoạt chưa (console hiển thị `TRẠNG THÁI: ĐANG CHẠY`).
    - Kiểm tra xem cửa sổ Genshin Impact có đang được chọn (Active) hay không.
    - Kiểm tra trong game mục **Cài đặt > Khác > Tự Động Phát Cốt Truyện** đã chuyển thành **Tắt** chưa.
    - Đảm bảo game đang hiển thị trên màn hình chính (Primary Display) nếu dùng nhiều màn hình.
- **Bị sai độ phân giải**:
    - Mở file `.env` và sửa lại thông số `WIDTH` và `HEIGHT` theo đúng độ phân giải màn hình của bạn.
