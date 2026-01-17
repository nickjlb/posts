@echo off
echo ========================================
echo Building Blog CMS Executable
echo ========================================
echo.

:: Check Python version
python --version
echo.

:: Install dependencies if not already installed
echo Installing dependencies...
pip install -r requirements.txt
echo.

:: Clean previous builds
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
if exist BlogCMS.spec del BlogCMS.spec

echo Building executable with PyInstaller...
echo This may take 2-3 minutes...
echo.

:: Create the executable
pyinstaller --name="BlogCMS" ^
    --onefile ^
    --noconsole ^
    --add-data "templates;templates" ^
    --add-data "static;static" ^
    --hidden-import=sqlite3 ^
    --hidden-import=werkzeug ^
    --hidden-import=jinja2 ^
    app.py

echo.
echo ========================================
echo Build Complete!
echo ========================================
echo.
if exist "dist\BlogCMS.exe" (
    echo SUCCESS! Your executable is ready:
    echo Location: dist\BlogCMS.exe
    echo.
    echo To run: Simply double-click BlogCMS.exe
    echo The executable is portable - you can move it anywhere!
    echo.
    echo Note: When you first run it, a blog.db and static/uploads
    echo folder will be created in the same directory as the .exe
) else (
    echo ERROR: Build failed! Check the output above for errors.
    echo.
    echo Common fixes:
    echo 1. Make sure Python 3.8+ is installed
    echo 2. Run: pip install -r requirements.txt
    echo 3. Try running as Administrator
)
echo.
pause
