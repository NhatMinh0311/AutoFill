@echo off
setlocal EnableDelayedExpansion

:: Kiểm tra Python 3
py -3 --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Python 3 is not installed. Downloading Python...
    
    :: Tải file cài đặt Python
    curl -o python-installer.exe https://www.python.org/ftp/python/3.13.2/python-3.13.2-amd64.exe
    
    :: Cài đặt Python tự động
    echo Installing Python...
    start /wait python-installer.exe /quiet InstallAllUsers=1 PrependPath=1
    
    echo Python has been installed. Please restart your computer and run this script again.
    pause
    exit
)

echo Python 3 is installed.

:: Lấy đường dẫn thư mục Scripts của Python
for /f "delims=" %%P in ('py -3 -c "import sys; from pathlib import Path; print(str(Path(sys.executable).parent / 'Scripts'))"') do set "PYTHON_SCRIPTS=%%P"

:: Thêm thư mục Scripts vào PATH nếu chưa có
echo %PATH% | findstr /I /C:"%PYTHON_SCRIPTS%" >nul 2>&1
if %errorlevel% neq 0 (
    echo Adding Python Scripts folder to PATH temporarily...
    set "PATH=%PATH%;%PYTHON_SCRIPTS%"
    echo Please add the following path to your system PATH manually:
    echo %PYTHON_SCRIPTS%
    pause
)

:: Cập nhật pip và cài đặt thư viện cần thiết
echo Installing required Python libraries...
py -3 -m pip install --upgrade pip
py -3 -m pip install selenium pdfplumber webdriver-manager tk

echo Library installation completed!
echo All setup is complete. You can now run your Python programs.

pause
