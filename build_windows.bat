@echo off
setlocal
py -3 -m pip install --upgrade pip
py -3 -m pip install -r requirements.txt
if errorlevel 1 exit /b 1
py -3 -m pip install pyinstaller
py -3 -m PyInstaller --noconfirm --clean --windowed --name SoloDesk --collect-all customtkinter solodesk.py
if errorlevel 1 exit /b 1
echo Build complete: dist\SoloDesk\SoloDesk.exe
pause
