@echo off
setlocal enabledelayedexpansion
cd /d "%~dp0"

echo [Glance] Chuan bi dong goi ung dung Glance cho Windows...

set "BUILD_PY="

:: 1. Uu tien dung moi truong ao .venv neu da duoc tao boi start_windows.bat
if exist ".venv\Scripts\python.exe" (
  set "BUILD_PY=.venv\Scripts\python.exe"
  echo [Glance] Su dung moi truong ao san co: .venv
)

:: 2. Neu chua co .venv, tu dong tim kiem phien ban Python phu hop nhat tren he thong
if "!BUILD_PY!"=="" (
  where py >nul 2>&1
  if not errorlevel 1 (
    for %%v in (-3.12 -3.13 -3.14 -3.11 -3.10 -3) do (
      if "!BUILD_PY!"=="" (
        py %%v -c "import tkinter" >nul 2>&1
        if not errorlevel 1 (
          set "BUILD_PY=py %%v"
        )
      )
    )
  )
)

if "!BUILD_PY!"=="" (
  where python >nul 2>&1
  if not errorlevel 1 (
    python -c "import sys; assert sys.version_info[0] == 3" >nul 2>&1
    if not errorlevel 1 (
      set "BUILD_PY=python"
    )
  )
)

if "!BUILD_PY!"=="" (
  echo [Loi] Khong tim thay Python 3 tren may.
  echo Vui long cai dat Python 3 tu https://www.python.org/downloads/windows/
  pause
  exit /b 1
)

echo [Glance] Dang kiem tra va cai dat thu vien dong goi...
!BUILD_PY! -m pip install -r requirements.txt
if errorlevel 1 (
  echo.
  echo [Loi] Khong the cai dat thu vien phu thuoc cho qua trinh build.
  echo Neu ban dang dung Python 3.14, thu vien opencv hoac pyinstaller co the chua ho tro wheel san.
  echo Hay thu cai them Python 3.12 hoac 3.13 de dong goi file .exe thanh cong.
  pause
  exit /b 1
)

echo [Glance] Dang tien hanh dong goi Glance.exe bang PyInstaller...
!BUILD_PY! -m PyInstaller --noconfirm --clean --windowed --onefile --name Glance --collect-data cv2 glance_windows.py
if errorlevel 1 goto :failed

echo.
echo =========================================================================
echo [THANH CONG] File ung dung doc lap da duoc tao tai:
echo %CD%\dist\Glance.exe
echo.
echo Ban co the copy file Glance.exe nay sang bat ky may Windows nao de chay
echo ma khong can cai them Python hay thu vien nao nua!
echo =========================================================================
echo.
pause
exit /b 0

:failed
echo.
echo =========================================================================
echo [Loi] Dong goi that bai. Vui long kiem tra thong bao loi chi tiet o tren.
echo =========================================================================
echo.
pause
exit /b 1
