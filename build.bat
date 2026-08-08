@echo off
echo ============================================
echo  Facebook Reel Downloader - Build Script
echo ============================================
echo.

echo [1/3] Installing dependencies...
pip install -r requirements.txt pyinstaller
if errorlevel 1 (
    echo ERROR: Failed to install dependencies
    pause
    exit /b 1
)

echo.
echo [2/3] Building executable with PyInstaller...
python -m PyInstaller --onefile --windowed --name "FacebookReelDownloader" --distpath "dist" --workpath "build" --specpath "." main.py
if errorlevel 1 (
    echo ERROR: Failed to build executable
    pause
    exit /b 1
)

echo.
echo [3/3] Building installer with Inno Setup...
"C:\Program Files (x86)\Inno Setup 6\ISCC.exe" installer.iss
if errorlevel 1 (
    echo ERROR: Failed to build installer
    pause
    exit /b 1
)

echo.
echo ============================================
echo  BUILD COMPLETE!
echo ============================================
echo  EXE:      dist\FacebookReelDownloader.exe
echo  Installer: installer\FacebookReelDownloader-Setup.exe
echo ============================================
pause
