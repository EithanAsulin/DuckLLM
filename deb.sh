#!/bin/bash

APP_NAME="DuckLLM"
VERSION="1.0.0"
DEB_DIR="DuckLLM_pkg"


echo "[*] Cleaning up..."
rm -rf build dist $DEB_DIR "${APP_NAME}.deb"


echo "[*] Running PyInstaller..."
python3 -m PyInstaller --name "DuckLLM" \
            --windowed \
            --noconfirm \
            --collect-all llama_cpp \
            --collect-all platformdirs \
            --collect-binaries llama_cpp \
            --exclude-module nvidia \
            --exclude-module tensorrt \
            --add-data "fullscreen.html:." \
            --add-data "Attachment.png:." \
            --add-data "Unfiltered.png:." \
            --add-data "Web.png:." \
            --add-data "duckllm_chat.json:." \
            --add-data "duckllm_settings.json:." \
            --add-data "Unfiltered_Instructions.txt:." \
            --add-data "DuckLLM.gguf:." \
            "DuckLLM.py"

echo "[*] Creating .deb structure..."
mkdir -p $DEB_DIR/opt/$APP_NAME
mkdir -p $DEB_DIR/usr/bin
mkdir -p $DEB_DIR/usr/share/applications
mkdir -p $DEB_DIR/usr/share/icons/hicolor/256x256/apps
mkdir -p $DEB_DIR/DEBIAN

cp -r dist/DuckLLM/* $DEB_DIR/opt/$APP_NAME/

cat <<EOF > $DEB_DIR/usr/bin/$APP_NAME
#!/bin/bash
/opt/$APP_NAME/DuckLLM "\$@"
EOF
chmod +x $DEB_DIR/usr/bin/$APP_NAME

cat <<EOF > $DEB_DIR/usr/share/applications/$APP_NAME.desktop
[Desktop Entry]
Name=DuckLLM
Exec=/usr/bin/$APP_NAME
Icon=$APP_NAME
Type=Application
Categories=Utility;Development;Productivity;Education;
Terminal=false
EOF

if [ -f "icon.png" ]; then
    cp icon.png $DEB_DIR/usr/share/icons/hicolor/256x256/apps/$APP_NAME.png
fi

cat <<EOF > $DEB_DIR/DEBIAN/control
Package: $APP_NAME
Version: $VERSION
Section: utils
Priority: optional
Architecture: $(dpkg --print-architecture)
Maintainer: Duck Inc. (Eithan Asulin) duckinc68@gmail.com
Description: DuckLLM is a local AI assistant that runs on your machine, providing fast and private interactions with your data. It supports text, images, and files, making it a versatile tool for various tasks.
EOF


echo "[*] Finalizing .deb package..."
dpkg-deb --build $DEB_DIR "${APP_NAME}_${VERSION}_$(dpkg --print-architecture).deb"



echo "[+] Done! You can install it with: sudo apt install ./${APP_NAME}_${VERSION}_$(dpkg --print-architecture).deb"