@echo off
setlocal
cd /d "%~dp0"
py -3 -m pip install -r requirements.txt
if errorlevel 1 goto :failed
py -3 -m PyInstaller --noconfirm --clean --windowed --onefile --name Glance --collect-data cv2 glance_windows.py
if errorlevel 1 goto :failed
echo.
echo Build completed: %CD%\dist\Glance.exe
pause
exit /b 0
:failed
echo.
echo Build failed. See the error above.
pause
exit /b 1
