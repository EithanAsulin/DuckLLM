#!/bin/zsh

echo "[*] Cleaning up old builds..."
rm -rf build dist dmg_staging "DuckLLM.dmg" icon.icns icon.iconset


if [ -f "icon.png" ]; then
    echo "[*] Converting icon.png to .icns... (annoying ass apple)"
    mkdir -p icon.iconset
    sips -z 16 16     icon.png --out icon.iconset/icon_16x16.png > /dev/null 2>&1
    sips -z 32 32     icon.png --out icon.iconset/icon_16x16@2x.png > /dev/null 2>&1
    sips -z 32 32     icon.png --out icon.iconset/icon_32x32.png > /dev/null 2>&1
    sips -z 64 64     icon.png --out icon.iconset/icon_32x32@2x.png > /dev/null 2>&1
    sips -z 128 128   icon.png --out icon.iconset/icon_128x128.png > /dev/null 2>&1
    sips -z 256 256   icon.png --out icon.iconset/icon_128x128@2x.png > /dev/null 2>&1
    sips -z 256 256   icon.png --out icon.iconset/icon_256x256.png > /dev/null 2>&1
    sips -z 512 512   icon.png --out icon.iconset/icon_256x256@2x.png > /dev/null 2>&1
    sips -z 512 512   icon.png --out icon.iconset/icon_512x512.png > /dev/null 2>&1
    sips -z 1024 1024 icon.png --out icon.iconset/icon_512x512@2x.png > /dev/null 2>&1
    iconutil -c icns icon.iconset
    rm -rf icon.iconset
    ICON_FLAG="--icon=icon.icns"
fi

echo "[*] Running PyInstaller..."
python3 -m PyInstaller --name "DuckLLM" \
            --windowed \
            --noconfirm \
            $ICON_FLAG \
            --collect-all llama_cpp \
            --collect-binaries llama_cpp \
            --add-data "fullscreen.html:." \
            --add-data "Attachment.png:." \
            --add-data "Unfiltered.png:." \
            --add-data "Web.png:." \
            --add-data "duckllm_chat.json:." \
            --add-data "duckllm_settings.json:." \
            --add-data "Unfiltered_Instructions.txt:." \
            --add-data "DuckLLM.gguf:." \
            "DuckLLM.py"


codesign --force --deep --sign - "dist/DuckLLM.app"


echo "[*] Creating DMG layout..."
mkdir dmg_staging
cp -R "dist/DuckLLM.app" dmg_staging/
ln -s /Applications dmg_staging/Applications


echo "[*] Finalizing DMG..."
hdiutil create -volname "DuckLLM" -srcfolder dmg_staging -ov -format UDZO "DuckLLM Installer.dmg"


rm -f icon.icns

echo "[+] Done! DuckLLM Installer.dmg is ready."
