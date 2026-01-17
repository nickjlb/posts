@echo off
echo ========================================
echo Python 3.14+ Compatibility Test
echo ========================================
echo.

:: Check Python version
echo Checking Python version...
python --version
echo.

:: Test if Python is accessible
python -c "import sys; print(f'Python {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro} detected')"
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.8 or higher from python.org
    pause
    exit /b 1
)
echo.

:: Check if version is at least 3.8
python -c "import sys; exit(0 if sys.version_info >= (3, 8) else 1)"
if errorlevel 1 (
    echo ERROR: Python version is too old
    echo Blog CMS requires Python 3.8 or higher
    echo Please upgrade Python from python.org
    pause
    exit /b 1
)
echo ✓ Python version is compatible!
echo.

:: Test pip
echo Testing pip...
pip --version
if errorlevel 1 (
    echo ERROR: pip is not installed
    echo Please reinstall Python with pip included
    pause
    exit /b 1
)
echo ✓ pip is available!
echo.

:: Install dependencies
echo Installing dependencies...
pip install -r requirements.txt
if errorlevel 1 (
    echo ERROR: Failed to install dependencies
    echo Try running as Administrator
    pause
    exit /b 1
)
echo ✓ Dependencies installed successfully!
echo.

:: Test Flask import
echo Testing Flask...
python -c "import flask; print(f'Flask {flask.__version__} loaded successfully')"
if errorlevel 1 (
    echo ERROR: Flask import failed
    pause
    exit /b 1
)
echo ✓ Flask works!
echo.

:: Test the app
echo Testing Blog CMS app...
python -c "import app; app.init_db(); print('✓ Blog CMS initialized successfully')"
if errorlevel 1 (
    echo ERROR: Blog CMS failed to initialize
    pause
    exit /b 1
)
echo.

echo ========================================
echo ALL TESTS PASSED!
echo ========================================
echo.
echo Your system is ready to:
echo 1. Run the development server: python app.py
echo 2. Build the executable: build.bat
echo.
pause
