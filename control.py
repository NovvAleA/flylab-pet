#!/usr/bin/env python3
"""Small GTK control panel for the desktop fly."""

from __future__ import annotations

import os
import signal
import subprocess
from pathlib import Path

import gi
gi.require_version("Gtk", "3.0")
from gi.repository import GLib, Gtk  # noqa: E402

from appearances import APPEARANCES
from items import ITEMS
from settings import load_settings, save_settings


ROOT = Path(__file__).resolve().parent
RUNTIME = Path(os.environ.get("XDG_RUNTIME_DIR", "/tmp"))
PID_FILE = RUNTIME / "flylab-desktop-fly.pid"
LOG_FILE = RUNTIME / "flylab-desktop-fly.log"


def running_pid() -> int | None:
    try:
        pid = int(PID_FILE.read_text().strip())
        os.kill(pid, 0)
        return pid
    except (OSError, ValueError):
        PID_FILE.unlink(missing_ok=True)
    # Recover old/direct launches which predate the PID file. Checking cwd and
    # command line avoids touching unrelated Python applications.
    for process_dir in Path("/proc").glob("[0-9]*"):
        try:
            if process_dir.joinpath("cwd").resolve() != ROOT:
                continue
            command = process_dir.joinpath("cmdline").read_bytes().replace(b"\0", b" ")
            if b"app.py" in command:
                pid = int(process_dir.name)
                PID_FILE.write_text(str(pid))
                return pid
        except (OSError, ValueError):
            continue
    return None


def set_running(enabled: bool) -> None:
    pid = running_pid()
    if enabled and pid is None:
        log = LOG_FILE.open("ab")
        process = subprocess.Popen(
            [str(ROOT / "run.sh")], stdin=subprocess.DEVNULL,
            stdout=log, stderr=subprocess.STDOUT, start_new_session=True,
        )
        log.close()
        PID_FILE.write_text(str(process.pid))
    elif not enabled and pid is not None:
        os.kill(pid, signal.SIGTERM)
        PID_FILE.unlink(missing_ok=True)


class ControlWindow(Gtk.ApplicationWindow):
    def __init__(self, app):
        super().__init__(application=app, title="FlyLab — пульт мухи")
        self.set_default_size(470, 390)
        self.set_border_width(22)
        self._updating = False

        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=18)
        self.add(box)
        title = Gtk.Label()
        title.set_markup("<span size='x-large' weight='bold'>Пульт мухи</span>")
        title.set_xalign(0)
        box.pack_start(title, False, False, 0)
        subtitle = Gtk.Label(label="Настройки применяются сразу и сохраняются.")
        subtitle.set_xalign(0)
        box.pack_start(subtitle, False, False, 0)

        grid = Gtk.Grid(column_spacing=18, row_spacing=15)
        box.pack_start(grid, False, False, 0)
        grid.attach(Gtk.Label(label="Запустить муху", xalign=0), 0, 0, 1, 1)
        self.power = Gtk.Switch(active=running_pid() is not None)
        self.power.connect("notify::active", self.on_power)
        grid.attach(self.power, 1, 0, 1, 1)

        settings = load_settings()
        self.appearance = self.make_combo(APPEARANCES, settings.get("appearance", "fly"))
        self.left = self.make_combo(settings.get("left_item", "coffee"))
        self.right = self.make_combo(settings.get("right_item", "cigarette"))
        grid.attach(Gtk.Label(label="Насекомое", xalign=0), 0, 1, 1, 1)
        grid.attach(self.appearance, 1, 1, 1, 1)
        grid.attach(Gtk.Label(label="Предмет в левой лапе", xalign=0), 0, 2, 1, 1)
        grid.attach(self.left, 1, 2, 1, 1)
        grid.attach(Gtk.Label(label="Предмет в правой лапе", xalign=0), 0, 3, 1, 1)
        grid.attach(self.right, 1, 3, 1, 1)
        self.speed = Gtk.Scale.new_with_range(Gtk.Orientation.HORIZONTAL, 0.25, 3.0, 0.05)
        self.speed.set_value(float(settings.get("speed_multiplier", 1.0)))
        self.speed.set_digits(2)
        self.speed.set_value_pos(Gtk.PositionType.RIGHT)
        self.speed.set_hexpand(True)
        for value, label in ((0.5, "0,5×"), (1.0, "1×"), (2.0, "2×"), (3.0, "3×")):
            self.speed.add_mark(value, Gtk.PositionType.BOTTOM, label)
        grid.attach(Gtk.Label(label="Скорость", xalign=0), 0, 4, 1, 1)
        grid.attach(self.speed, 1, 4, 1, 1)
        self.appearance.connect("changed", self.on_settings_changed)
        self.left.connect("changed", self.on_settings_changed)
        self.right.connect("changed", self.on_settings_changed)
        self.speed.connect("value-changed", self.on_settings_changed)

        self.stop_button = Gtk.Button(label="⏹  Полностью отключить муху")
        self.stop_button.get_style_context().add_class("destructive-action")
        self.stop_button.connect("clicked", self.on_stop_clicked)
        box.pack_start(self.stop_button, False, False, 0)

        note = Gtk.Label(label="Пчела может залетать в улей; её мозг остаётся прежним.")
        note.set_xalign(0)
        note.get_style_context().add_class("dim-label")
        box.pack_end(note, False, False, 0)
        GLib.timeout_add(1000, self.refresh_power)

    def make_combo(self, registry_or_selected, selected=None):
        registry = registry_or_selected if selected is not None else ITEMS
        selected = selected if selected is not None else registry_or_selected
        combo = Gtk.ComboBoxText()
        for entry in registry.values():
            combo.append(entry.key, entry.title)
        combo.set_active_id(selected if selected in registry else next(iter(registry)))
        combo.set_hexpand(True)
        return combo

    def on_power(self, switch, _param):
        if not self._updating:
            set_running(switch.get_active())

    def on_stop_clicked(self, _button):
        set_running(False)
        self._updating = True
        self.power.set_active(False)
        self._updating = False

    def on_settings_changed(self, *_args):
        save_settings({
            "appearance": self.appearance.get_active_id(),
            "speed_multiplier": round(self.speed.get_value(), 2),
            "left_item": self.left.get_active_id(),
            "right_item": self.right.get_active_id(),
        })

    def refresh_power(self):
        active = running_pid() is not None
        if self.power.get_active() != active:
            self._updating = True
            self.power.set_active(active)
            self._updating = False
        self.stop_button.set_sensitive(active)
        return True


class ControlApp(Gtk.Application):
    def __init__(self):
        super().__init__(application_id="ai.flylab.DesktopFlyControl")

    def do_activate(self):
        window = self.props.active_window or ControlWindow(self)
        window.show_all()
        window.present()


if __name__ == "__main__":
    ControlApp().run(None)
