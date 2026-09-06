@echo off
echo ============================================
echo  Facebook Reel Downloader - Build Script
echo  Building x86 + x64
echo ============================================
echo.

echo [1/5] Installing dependencies...
py -3.14 -m pip install -r requirements.txt pyinstaller
if errorlevel 1 (
    echo ERROR: Failed to install dependencies for x64
    pause
    exit /b 1
)
py -3.12-32 -m pip install -r requirements.txt pyinstaller
if errorlevel 1 (
    echo ERROR: Failed to install dependencies for x86
    pause
    exit /b 1
)

echo.
echo [2/5] Building x86 executable...
py -3.12-32 -m PyInstaller --onefile --windowed --name "FacebookReelDownloader" --distpath "dist\x86" --workpath "build\x86" --specpath "." --icon "media\icon.ico" --add-data "media\icon.ico;media" main.py
if errorlevel 1 (
    echo ERROR: Failed to build x86 executable
    pause
    exit /b 1
)

echo.
echo [3/5] Building x64 executable...
py -3.14 -m PyInstaller --onefile --windowed --name "FacebookReelDownloader" --distpath "dist\x64" --workpath "build\x64" --specpath "." --icon "media\icon.ico" --add-data "media\icon.ico;media" main.py
if errorlevel 1 (
    echo ERROR: Failed to build x64 executable
    pause
    exit /b 1
)

echo.
echo [4/5] Building x86 installer...
"C:\Program Files (x86)\Inno Setup 6\ISCC.exe" /DARCH=x86 installer.iss
if errorlevel 1 (
    echo ERROR: Failed to build x86 installer
    pause
    exit /b 1
)

echo.
echo [5/5] Building x64 installer...
"C:\Program Files (x86)\Inno Setup 6\ISCC.exe" /DARCH=x64 installer.iss
if errorlevel 1 (
    echo ERROR: Failed to build x64 installer
    pause
    exit /b 1
)

echo.
echo ============================================
echo  BUILD COMPLETE!
echo ============================================
echo  x86 EXE:      dist\x86\FacebookReelDownloader.exe
echo  x64 EXE:      dist\x64\FacebookReelDownloader.exe
echo  x86 Installer: installer\FacebookReelDownloader-Setup-x86.exe
echo  x64 Installer: installer\FacebookReelDownloader-Setup-x64.exe
echo ============================================
pause
