@echo off
set APP_NAME=DuckLLM

echo [*] Cleaning up old builds...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
if exist "%APP_NAME%_Windows.zip" del "%APP_NAME%_Windows.zip"

echo [*] Installing PyInstaller and Image tools...
pip install pyinstaller Pillow

echo [*] NUCLEAR FIX: Downloading stubborn modules directly to your project folder...
pip install typing_extensions --target . --upgrade

echo [*] Converting icon...
if exist "icon.png" (
    python -c "from PIL import Image; img = Image.open('icon.png').convert('RGBA'); img.save('icon.ico', format='ICO', sizes=[(256, 256), (128, 128), (64, 64), (48, 48), (32, 32), (16, 16)])"
)

set ICON_CMD=
if exist "icon.ico" set ICON_CMD=--icon "icon.ico"

echo [*] Running PyInstaller...
python -m PyInstaller --name "%APP_NAME%" ^
    --windowed ^
    --noconfirm ^
    --collect-all llama_cpp ^
    --collect-all platformdirs ^
    --collect-all typing_extensions ^
    --exclude-module nvidia ^
    --exclude-module tensorrt ^
    --add-data "fullscreen.html;." ^
    --add-data "Attachment.png;." ^
    --add-data "Unfiltered.png;." ^
    --add-data "Web.png;." ^
    --add-data "duckllm_chat.json;." ^
    --add-data "duckllm_settings.json;." ^
    --add-data "Unfiltered_Instructions.txt;." ^
    --add-data "DuckLLM.gguf;." ^
    %ICON_CMD% ^
    "DuckLLM.py"

echo [*] This Purely Produces And exe And A Folder With The Data, Please Use Inno Setup To Create An Installer If You Want One.
pause