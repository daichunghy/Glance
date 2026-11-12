@echo off
setlocal enabledelayedexpansion
chcp 65001 >nul 2>&1
cd /d "%~dp0"

:: ============================================================================
:: 0. Neu co san file Glance.exe da dong goi doc lap thi mo ngay lap tuc!
:: ============================================================================
if exist "Glance.exe" (
  start "" "Glance.exe" %*
  exit /b 0
)
if exist "dist\Glance.exe" (
  start "" "dist\Glance.exe" %*
  exit /b 0
)

:: ============================================================================
:: 1. Kiem tra xem nguoi dung co dang mo truc tiep trong file .zip chua giai nen
:: ============================================================================
if not exist "glance_windows.py" (
  echo.
  echo =========================================================================
  echo [THONG BAO] Ban dang mo truc tiep ben trong file nen .zip!
  echo.
  echo Cach mo dung:
  echo 1. Quay lai thu muc Tai ve ^(Downloads^).
  echo 2. Nhap chuot phai vao file Glance-Windows.zip -^> chon "Extract All..."
  echo    ^(Trich xuat tat ca^).
  echo 3. Mo thu muc vua giai nen va bam dup vao start_windows.bat.
  echo =========================================================================
  echo.
  pause
  exit /b 1
)

echo [Glance] Dang kiem tra moi truong khoi chay...

:: ============================================================================
:: 2. Neu da co san moi truong ao .venv hop le tu lan chay truoc -> chay luon
:: ============================================================================
if exist ".venv\Scripts\python.exe" (
  ".venv\Scripts\python.exe" -c "import cv2, tkinter" >nul 2>&1
  if not errorlevel 1 (
    echo [Glance] Dang mo ung dung Glance...
    if exist ".venv\Scripts\pythonw.exe" (
      start "" ".venv\Scripts\pythonw.exe" glance_windows.py %*
      exit /b 0
    ) else (
      ".venv\Scripts\python.exe" glance_windows.py %*
      exit /b 0
    )
  )
)

set "GLANCE_PYTHON_CMD="

:: ============================================================================
:: 3. Tim Python tren may: ho tro moi phien ban tu Python 3.8 den 3.14+
::    (Ưu tien 3.12, 3.11, 3.13, 3.10, 3.9, 3.8, 3.14, va mac dinh -3)
:: ============================================================================
where py >nul 2>&1
if not errorlevel 1 (
  for %%v in (-3.12 -3.11 -3.13 -3.10 -3.9 -3.8 -3.14 -3) do (
    if "!GLANCE_PYTHON_CMD!"=="" (
      py %%v -c "import sys, tkinter; assert sys.version_info >= (3, 8)" >nul 2>&1
      if not errorlevel 1 (
        set "GLANCE_PYTHON_CMD=py %%v"
      )
    )
  )
)

:: 4. Tim python trong PATH (bo qua stub WindowsApps cua Microsoft Store)
if "!GLANCE_PYTHON_CMD!"=="" (
  for /f "delims=" %%p in ('where python 2^>nul') do (
    if "!GLANCE_PYTHON_CMD!"=="" (
      echo "%%~p" | findstr /i "WindowsApps" >nul
      if errorlevel 1 (
        "%%~p" -c "import sys, tkinter; assert sys.version_info >= (3, 8)" >nul 2>&1
        if not errorlevel 1 (
          set "GLANCE_PYTHON_CMD="%%~p""
        )
      )
    )
  )
)

:: 5. Quet truc tiep cac thu muc cai Python pho bien (ke ca khi quen Add to PATH)
if "!GLANCE_PYTHON_CMD!"=="" (
  for %%d in (
    "%LocalAppData%\Programs\Python\Python312"
    "%LocalAppData%\Programs\Python\Python311"
    "%LocalAppData%\Programs\Python\Python313"
    "%LocalAppData%\Programs\Python\Python310"
    "%LocalAppData%\Programs\Python\Python39"
    "%LocalAppData%\Programs\Python\Python38"
    "%ProgramFiles%\Python312"
    "%ProgramFiles%\Python311"
    "%ProgramFiles%\Python313"
    "%ProgramFiles%\Python310"
    "%ProgramFiles%\Python39"
    "%ProgramFiles%\Python38"
    "C:\Python312"
    "C:\Python311"
    "C:\Python310"
    "C:\Python39"
    "C:\Python38"
  ) do (
    if "!GLANCE_PYTHON_CMD!"=="" (
      if exist "%%~d\python.exe" (
        "%%~d\python.exe" -c "import sys, tkinter; assert sys.version_info >= (3, 8)" >nul 2>&1
        if not errorlevel 1 (
          set "GLANCE_PYTHON_CMD="%%~d\python.exe""
        )
      )
    )
  )
)

:: ============================================================================
:: 6. Neu may KHONG co Python hoac Python qua cu (< 3.8):
::    TU DONG tai va cai dat Python 3.12 (kem Tkinter + pip) cho nguoi dung!
:: ============================================================================
if "!GLANCE_PYTHON_CMD!"=="" (
  echo.
  echo =========================================================================
  echo [Glance] May cua ban chua co Python phu hop.
  echo Glance se TU DONG tai va cai dat moi truong Python 3.12 cho ban
  echo ^(Chi mat khoang 1 phut trong lan dau tien mở app, khong can thao tac gi^)...
  echo =========================================================================
  echo.

  :: Thu 1: Dung winget neu Windows 10/11 co san
  where winget >nul 2>&1
  if not errorlevel 1 (
    echo [Glance] Dang cai dat Python 3.12 qua Windows Package Manager ^(winget^)...
    winget install -e --id Python.Python.3.12 --scope user --silent --accept-package-agreements --accept-source-agreements >nul 2>&1
    if exist "%LocalAppData%\Programs\Python\Python312\python.exe" (
      set "GLANCE_PYTHON_CMD="%LocalAppData%\Programs\Python\Python312\python.exe""
    )
  )

  :: Thu 2: Tai truc tiep bo cai Python 3.12.8 chinh thuc tu python.org va cai silent
  if "!GLANCE_PYTHON_CMD!"=="" (
    echo [Glance] Dang tai bo cai Python 3.12 chinh thuc tu python.org...
    set "PY_INSTALLER=%TEMP%\glance_python_3.12_setup.exe"
    powershell -NoProfile -ExecutionPolicy Bypass -Command "[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; Invoke-WebRequest -Uri 'https://www.python.org/ftp/python/3.12.8/python-3.12.8-amd64.exe' -OutFile $env:PY_INSTALLER -UseBasicParsing"
    if not exist "!PY_INSTALLER!" (
      where curl.exe >nul 2>&1
      if not errorlevel 1 (
        curl.exe -fsSL -o "!PY_INSTALLER!" "https://www.python.org/ftp/python/3.12.8/python-3.12.8-amd64.exe" >nul 2>&1
      )
    )
    if exist "!PY_INSTALLER!" (
      echo [Glance] Dang cai dat Python 3.12 ^(che do tu dong, khong can quyen Admin^)...
      "!PY_INSTALLER!" /quiet InstallAllUsers=0 PrependPath=1 Include_test=0 Include_tcltk=1 Include_pip=1 Include_launcher=1
      del /f /q "!PY_INSTALLER!" >nul 2>&1
      if exist "%LocalAppData%\Programs\Python\Python312\python.exe" (
        set "GLANCE_PYTHON_CMD="%LocalAppData%\Programs\Python\Python312\python.exe""
      )
    )
  )
)

if "!GLANCE_PYTHON_CMD!"=="" goto missing

echo [Glance] Su dung moi truong Python: !GLANCE_PYTHON_CMD!

:: ============================================================================
:: 7. Khoi tao Virtual Environment (.venv) va cai dat thu vien
:: ============================================================================
if exist ".venv\Scripts\python.exe" (
  ".venv\Scripts\python.exe" -c "import sys, tkinter; assert sys.version_info >= (3, 8)" >nul 2>&1
  if errorlevel 1 (
    echo [Glance] Phat hien .venv cu khong hop le, dang tao lai...
    rmdir /s /q .venv >nul 2>&1
  )
)

if not exist ".venv\Scripts\python.exe" (
  echo [Glance] Dang khoi tao moi truong ao .venv...
  !GLANCE_PYTHON_CMD! -m venv .venv
  if errorlevel 1 (
    echo [Glance] Chay truc tiep khong qua .venv...
    !GLANCE_PYTHON_CMD! -m pip install --user --disable-pip-version-check "opencv-python>=4.8,<5"
    !GLANCE_PYTHON_CMD! glance_windows.py %*
    if errorlevel 1 goto failed_run
    exit /b 0
  )
)

echo [Glance] Dang chuan bi thu vien camera ^(opencv-python^)...
".venv\Scripts\python.exe" -m pip install --disable-pip-version-check --only-binary=:all: "opencv-python>=4.8,<5"
if errorlevel 1 (
  ".venv\Scripts\python.exe" -m pip install --disable-pip-version-check "opencv-python>=4.8,<5"
  if errorlevel 1 goto failed_deps
)

echo [Glance] Dang khoi chay ung dung Glance...
if exist ".venv\Scripts\pythonw.exe" (
  start "" ".venv\Scripts\pythonw.exe" glance_windows.py %*
  exit /b 0
)
".venv\Scripts\python.exe" glance_windows.py %*
if errorlevel 1 goto failed_run

exit /b 0

:missing
echo.
echo =========================================================================
echo [THONG BAO] Khong the tu dong tai Python ^(kiem tra ket noi mang Internet^).
echo.
echo Vui long tai va cai dat Python 3 ^(ban 3.10, 3.11 hoac 3.12^) tai:
echo https://www.python.org/downloads/windows/
echo.
echo * Luu y khi cai: Tich chon "Add python.exe to PATH" rồi chay lai file nay.
echo =========================================================================
echo.
pause
exit /b 1

:failed_deps
echo.
echo =========================================================================
echo [CANH BAO] Khong the tai thu vien opencv-python ^(kiem tra ket noi mang^).
echo.
echo Hay dam bao may tinh dang ket noi Internet roi bam dup chay lai
echo start_windows.bat nhe!
echo =========================================================================
echo.
pause
exit /b 1

:failed_run
echo.
echo =========================================================================
echo [Loi] Glance khong the khoi chay. Vui long kiem tra thong bao o tren.
echo =========================================================================
echo.
pause
exit /b 1
