@echo off
echo ========================================
echo Building Blog CMS Executable
echo ========================================
echo.

:: Create the executable
pyinstaller --name="BlogCMS" ^
    --onefile ^
    --windowed ^
    --icon=NONE ^
    --add-data "templates;templates" ^
    --add-data "static;static" ^
    --hidden-import=sqlite3 ^
    app.py

echo.
echo ========================================
echo Build Complete!
echo ========================================
echo.
echo Your executable is in the 'dist' folder: dist\BlogCMS.exe
echo.
echo To run: Simply double-click BlogCMS.exe
echo.
pause
