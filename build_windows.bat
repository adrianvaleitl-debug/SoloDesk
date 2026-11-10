@echo off
setlocal
py -3 -m pip install --upgrade pyinstaller
py -3 -m PyInstaller --noconfirm --clean --windowed --name SoloDesk solodesk.py
if errorlevel 1 exit /b 1
echo Build complete: dist\SoloDesk\SoloDesk.exe
pause
