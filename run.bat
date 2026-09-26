@echo off
pushd "%~dp0"

:: ============================================
:: Kiem tra quyen Administrator
:: ============================================
echo Dang kiem tra quyen Administrator...
net session >nul 2>&1
if %errorlevel% neq 0 (
    color 0C
    echo.
    echo [LOI] Script nay yeu cau quyen Administrator!
    echo Vui long nhap chuot phai vao file run.bat va chon "Run as administrator"
    echo.
    goto end
)
color 0A
echo [OK] Dang chay voi quyen Administrator.
echo.

:: ============================================
:: Kiem tra cai dat Python
:: ============================================
color 0E
echo Dang kiem tra Python tren may...
python --version >nul 2>nul
if %errorlevel% neq 0 (
    color 0C
    echo.
    echo [LOI] Chua cai dat Python hoac chua them vao PATH!
    echo Vui long cai dat Python 3.11 tro len tu: https://www.python.org/downloads/
    echo Hay nho tich chon "Add Python to PATH" khi cai dat.
    echo.
    goto end
)

for /f "tokens=*" %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i
color 0A
echo [OK] Da tim thay %PYTHON_VERSION%
echo.

:: ============================================
:: Kiem tra trinh quan ly goi UV
:: ============================================
color 0E
echo Dang kiem tra trinh quan ly goi uv...
where uv >nul 2>nul
if %errorlevel% equ 0 (
    for /f "tokens=*" %%i in ('uv --version 2^>^&1') do set UV_VERSION=%%i
    color 0A
    echo [OK] Da tim thay %UV_VERSION%
    echo.
    goto run_script
)

echo Chua co uv. Dang tien hanh cai dat uv bang pip...
pip install uv
if %errorlevel% neq 0 (
    color 0C
    echo.
    echo [LOI] Khong the cai dat uv tu dong.
    echo Vui long kiem tra ket noi mang hoac go lenh: pip install uv
    echo.
    goto end
)
color 0A
echo [OK] Da cai dat uv thanh cong!
echo.

:: ============================================
:: Khoi chay script Python
:: ============================================
:run_script
color 0B
echo ============================================
echo Dang khoi chay Tool Tu Dong Bo Qua Hoi Thoai...
echo ============================================
echo.
color 0F

uv run autoskip_dialogue.py
set SCRIPT_EXIT_CODE=%errorlevel%

echo.
if %SCRIPT_EXIT_CODE% equ 0 (
    color 0A
    echo ============================================
    echo [THANH CONG] Chuong trinh da ket thuc!
    echo ============================================
    echo.
    goto end
) else (
    color 0C
    echo ============================================
    echo [LOI] Chuong trinh ket thuc voi ma loi: %SCRIPT_EXIT_CODE%
    echo ============================================
    echo.
    goto retry_prompt
)

:: ============================================
:: Tuy chon thu lai
:: ============================================
:retry_prompt
color 0E
set /p RETRY="Ban co muon thu chay lai khong? (Y/N): "
if /i "%RETRY%"=="Y" goto run_script
if /i "%RETRY%"=="YES" goto run_script
echo.
echo Dang thoat...
goto end

:end
color 0F
@pause
