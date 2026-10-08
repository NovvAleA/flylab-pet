#!/bin/sh
set -eu

PROJECT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
DATA_HOME=${XDG_DATA_HOME:-"$HOME/.local/share"}
INSTALL_DIR="$DATA_HOME/flylab-pet"
APPLICATIONS_DIR="$DATA_HOME/applications"
BIN_DIR=${FLYLAB_BIN_DIR:-"$HOME/.local/bin"}

check_python_dependencies() {
    /usr/bin/python3 -c '
import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk
from PIL import Image, ImageGrab
' >/dev/null 2>&1
}

if ! check_python_dependencies; then
    if command -v apt-get >/dev/null 2>&1 && command -v sudo >/dev/null 2>&1; then
        echo "FlyLab: устанавливаю системные зависимости GTK/Pillow..."
        sudo apt-get update
        sudo apt-get install -y python3 python3-gi gir1.2-gtk-3.0 python3-pil
    else
        echo "Не найдены GTK 3/Pillow. Установите python3-gi, gir1.2-gtk-3.0 и python3-pil." >&2
        exit 1
    fi
fi

mkdir -p "$INSTALL_DIR/assets" "$APPLICATIONS_DIR" "$BIN_DIR"
for file in app.py appearances.py brain.py control.py desktop_scene.py items.py settings.py vision.py stimuli.json run.sh toggle.sh flylab-fly.svg; do
    cp "$PROJECT_DIR/$file" "$INSTALL_DIR/$file"
done
cp "$PROJECT_DIR"/assets/*.png "$INSTALL_DIR/assets/"
chmod +x "$INSTALL_DIR/run.sh" "$INSTALL_DIR/toggle.sh" "$INSTALL_DIR/control.py"

sed "s|@INSTALL_DIR@|$INSTALL_DIR|g" "$PROJECT_DIR/flylab-desktop-fly.desktop" \
    > "$APPLICATIONS_DIR/flylab-desktop-fly.desktop"
chmod +x "$APPLICATIONS_DIR/flylab-desktop-fly.desktop"

sed "s|@INSTALL_DIR@|$INSTALL_DIR|g" > "$BIN_DIR/flylab-pet" <<'EOF'
#!/bin/sh
exec /usr/bin/python3 "@INSTALL_DIR@/control.py" "$@"
EOF
chmod +x "$BIN_DIR/flylab-pet"

if command -v update-desktop-database >/dev/null 2>&1; then
    update-desktop-database "$APPLICATIONS_DIR" >/dev/null 2>&1 || true
fi

echo "FlyLab Pet установлен."
echo "Запуск: найдите «FlyLab — пульт мухи» в меню или выполните $BIN_DIR/flylab-pet"
