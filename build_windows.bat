@echo off
setlocal
py -3 -m pip install --upgrade pip
py -3 -m pip install -r requirements.txt
if errorlevel 1 exit /b 1
py -3 -m pip install pyinstaller pillow
py -3 tools\\generate_icon.py
py -3 -m PyInstaller --noconfirm --clean --windowed --name SoloDesk --icon assets\\solodesk.ico --add-data "assets\\solodesk.ico;." --collect-all customtkinter solodesk.py
if errorlevel 1 exit /b 1
echo Build complete: dist\SoloDesk\SoloDesk.exe
pause
