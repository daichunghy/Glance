@echo off
echo ========================================
echo   Building Glance for Windows (.exe)
echo ========================================

pip install -r requirements.txt

pyinstaller --noconsole --onefile --name Glance ^
    --add-data "%LOCALAPPDATA%\Programs\Python\Python311\Lib\site-packages\cv2\data;cv2/data" ^
    glance_windows.py

echo.
echo ========================================
echo   Build complete! Output: dist\Glance.exe
echo ========================================
pause
