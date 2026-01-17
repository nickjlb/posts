# Windows Installation Guide

This guide will help you build the Blog CMS executable on Windows.

## Prerequisites

1. **Python 3.8+ (including Python 3.14)**
   - Download from: https://www.python.org/downloads/
   - **✓ Tested and compatible with Python 3.14**
   - During installation, CHECK the box "Add Python to PATH"
   - Verify installation: Open Command Prompt and type `python --version`

2. **pip** (comes with Python)
   - Verify: `pip --version`

## Quick Test (Recommended)

Before building, verify your system is ready:

```bash
test_setup.bat
```

This will check Python version, install dependencies, and verify everything works!

## Step-by-Step Build Instructions

### 1. Download the Source Code

Download and extract the Blog CMS source code to a folder (e.g., `C:\BlogCMS`)

### 2. Open Command Prompt

- Press `Windows + R`
- Type `cmd` and press Enter
- Navigate to your folder:
  ```
  cd C:\BlogCMS
  ```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

This will install:
- Flask (web framework)
- Werkzeug (utilities)
- PyInstaller (creates the .exe file)

### 4. Build the Executable

Simply run:

```bash
build.bat
```

The script will:
- Create a standalone executable
- Bundle all templates and assets
- Output to the `dist` folder

**Build time**: About 1-2 minutes

### 5. Find Your Executable

After the build completes:
- Navigate to the `dist` folder
- You'll find `BlogCMS.exe`
- This is your complete, portable blog CMS!

### 6. Run It

- Double-click `BlogCMS.exe`
- Your browser will open automatically
- Start blogging!

## Alternative: Run Without Building

If you don't want to build an executable, you can run directly:

```bash
python app.py
```

Then visit `http://127.0.0.1:5000/cms` in your browser.

## Troubleshooting

### "python is not recognized..."

- Python isn't in your PATH
- Reinstall Python and check "Add Python to PATH"
- Or manually add Python to PATH in System Environment Variables

### "pip is not recognized..."

- pip isn't in your PATH
- Usually fixed by reinstalling Python with PATH option
- Or try: `python -m pip install -r requirements.txt`

### Build fails with "No module named..."

```bash
pip install --upgrade pip
pip install -r requirements.txt --force-reinstall
```

### Executable is too large

This is normal! PyInstaller bundles Python and all dependencies.
- Expected size: 20-40 MB
- It's completely self-contained - that's why it's portable!

### Antivirus flags the .exe

This is a false positive common with PyInstaller.
- Add an exception in your antivirus
- Or run directly with `python app.py` instead

## Distribution

To share your executable:

1. **Just the .exe**: Send `BlogCMS.exe` to anyone
2. **With existing blog**: Include `blog.db` and `static/uploads/` folder

Recipients just double-click to run - no installation needed!

## Updates

To rebuild with changes:

1. Make your changes to the source files
2. Run `build.bat` again
3. New executable will be in `dist` folder

---

**Need Help?** Check the main README.md file for more information.
