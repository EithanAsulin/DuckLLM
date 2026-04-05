#!/bin/bash

# Snaps are so god damn annoying lmao

WRITABLE_APP_DIR="$SNAP_USER_COMMON/DuckLLM_App"

if [ ! -d "$WRITABLE_APP_DIR" ] || [ "$SNAP_REVISION" != "$(cat $WRITABLE_APP_DIR/.snap_rev 2>/dev/null)" ]; then
    echo "Setting up writable application directory..."
    rm -rf "$WRITABLE_APP_DIR"
    cp -R "$SNAP/opt/DuckLLM" "$WRITABLE_APP_DIR"
    
    echo "$SNAP_REVISION" > "$WRITABLE_APP_DIR/.snap_rev"
fi

export LD_LIBRARY_PATH="$SNAP/usr/lib/x86_64-linux-gnu:$WRITABLE_APP_DIR:$LD_LIBRARY_PATH"

cd "$WRITABLE_APP_DIR"

exec "$WRITABLE_APP_DIR/DuckLLM" "$@"
