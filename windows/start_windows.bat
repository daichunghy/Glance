@echo off
setlocal
cd /d "%~dp0"
where py >nul 2>&1
if errorlevel 1 goto missing
py -3.12 -c "import tkinter" >nul 2>&1
if not errorlevel 1 (set "GLANCE_PY=3.12") else (
  py -3.11 -c "import tkinter" >nul 2>&1
  if errorlevel 1 goto missing
  set "GLANCE_PY=3.11"
)
if not exist ".venv\Scripts\python.exe" (
  py -%GLANCE_PY% -m venv .venv
  if errorlevel 1 goto failed
)
".venv\Scripts\python.exe" -m pip install "opencv-python>=4.8,<5"
if errorlevel 1 goto failed
".venv\Scripts\python.exe" glance_windows.py
if errorlevel 1 goto failed
exit /b 0
:missing
echo Glance requires Python 3.11 or 3.12 with tkinter and the Python Launcher.
echo Download Python from https://www.python.org/downloads/windows/
pause
exit /b 1
:failed
echo Glance could not start. Check the messages above and the camera permissions.
pause
exit /b 1
