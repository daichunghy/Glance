@echo off
setlocal enabledelayedexpansion
cd /d "%~dp0"

echo [Glance] Dang kiem tra moi truong Python...

set "GLANCE_PYTHON_CMD="

:: 1. Uu tien phien ban on dinh (3.12, 3.13) truoc neu co san, sau do den 3.14, 3.11, 3.10, va -3
where py >nul 2>&1
if not errorlevel 1 (
  for %%v in (-3.12 -3.13 -3.14 -3.11 -3.10 -3) do (
    if "!GLANCE_PYTHON_CMD!"=="" (
      py %%v -c "import tkinter" >nul 2>&1
      if not errorlevel 1 (
        set "GLANCE_PYTHON_CMD=py %%v"
      )
    )
  )
)

:: 2. Neu chua tim thay qua py launcher, thu truc tiep lenh python trong PATH
if "!GLANCE_PYTHON_CMD!"=="" (
  where python >nul 2>&1
  if not errorlevel 1 (
    python -c "import sys, tkinter; assert sys.version_info[0] == 3" >nul 2>&1
    if not errorlevel 1 (
      set "GLANCE_PYTHON_CMD=python"
    )
  )
)

:: 3. Neu van chua co Python 3 co san tkinter
if "!GLANCE_PYTHON_CMD!"=="" goto missing

echo [Glance] Tim thay moi truong: !GLANCE_PYTHON_CMD!

:: 4. Kiem tra va khoi tao Virtual Environment (.venv)
if exist ".venv\Scripts\python.exe" (
  ".venv\Scripts\python.exe" -c "import sys" >nul 2>&1
  if errorlevel 1 (
    echo [Glance] Phat hien .venv cu khong hop le, dang tao lai...
    rmdir /s /q .venv >nul 2>&1
  )
)

if not exist ".venv\Scripts\python.exe" (
  echo [Glance] Dang tao moi truong ao .venv...
  !GLANCE_PYTHON_CMD! -m venv .venv
  if errorlevel 1 goto failed_venv
)

:: 5. Cai dat thu vien phu thuoc
echo [Glance] Dang kiem tra va cap nhat thu vien (opencv-python)...
".venv\Scripts\python.exe" -m pip install -r requirements.txt
if errorlevel 1 goto failed_deps

:: 6. Khoi chay Glance
echo [Glance] Khoi chay ung dung...
".venv\Scripts\python.exe" glance_windows.py %*
if errorlevel 1 goto failed_run

exit /b 0

:missing
echo.
echo =========================================================================
echo [THONG BAO] Glance can Python 3 (kem thu vien tkinter).
echo.
echo Vui long cai dat Python 3 (khuyen dung ban 3.12 hoac 3.13 de co wheel san) tai:
echo https://www.python.org/downloads/windows/
echo.
echo * Luu y khi cai: Tich chon "Add python.exe to PATH" va "tcl/tk and IDLE".
echo =========================================================================
echo.
pause
exit /b 1

:failed_deps
echo.
echo =========================================================================
echo [CANH BAO] Khong the cai dat thu vien opencv-python vao moi truong nay.
echo.
echo Neu ban dang su dung Python 3.14 (ban thu nghiem/preview):
echo Thu vien OpenCV co the chua phat hanh ban binary wheel san cho Python 3.14.
echo.
echo Giai phap:
echo 1. Cai them Python 3.12 hoac 3.13 tu https://www.python.org/downloads/windows/
echo    roi chay lai file nay.
echo 2. Hoac chay build_exe.bat tren may da co san Glance.exe de dung doc lap.
echo =========================================================================
echo.
pause
exit /b 1

:failed_venv
echo.
echo [Loi] Khong the tao thu muc moi truong ao .venv.
echo Kiem tra quyen ghi hoac thu muc Glance tren may.
pause
exit /b 1

:failed_run
echo.
echo [Loi] Glance khong the khoi chay. Kiem tra quyen camera hoac ma loi o tren.
pause
exit /b 1
