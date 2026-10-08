#!/usr/bin/env python3
"""A lightweight screen-dwelling fly for X11/GTK 3."""

from __future__ import annotations

import argparse
import math
import os
import random
import time
from pathlib import Path

import gi
gi.require_version("Gtk", "3.0")
gi.require_version("Gdk", "3.0")
gi.require_version("GdkPixbuf", "2.0")
from gi.repository import Gdk, GdkPixbuf, GLib, Gtk  # noqa: E402
from PIL import Image, ImageDraw

from appearances import draw_appearance
from brain import TinyBrain
from desktop_scene import FlyQuest, fitted_asset
from items import draw_held_item
from settings import load_settings
from vision import LocalVision


ROOT = Path(__file__).resolve().parent
SPRITE_SIZE = 160
SPRITE_HALF = SPRITE_SIZE // 2
HIVE_WIDTH = 110
HIVE_HEIGHT = 120


def image_to_pixbuf(image: Image.Image) -> GdkPixbuf.Pixbuf:
    width, height = image.size
    return GdkPixbuf.Pixbuf.new_from_bytes(
        GLib.Bytes.new(image.tobytes()), GdkPixbuf.Colorspace.RGB, True, 8,
        width, height, width * 4,
    )


class HiveWindow(Gtk.Window):
    """A lightweight, click-through hive on the desktop."""

    def __init__(self, center_x: float, center_y: float):
        super().__init__(type=Gtk.WindowType.TOPLEVEL)
        self.set_title("FlyLab Hive")
        self.set_default_size(HIVE_WIDTH, HIVE_HEIGHT)
        self.set_size_request(HIVE_WIDTH, HIVE_HEIGHT)
        self.set_decorated(False)
        self.set_keep_above(True)
        self.set_skip_taskbar_hint(True)
        self.set_skip_pager_hint(True)
        self.set_accept_focus(False)
        self.set_app_paintable(True)
        visual = self.get_screen().get_rgba_visual()
        if visual:
            self.set_visual(visual)
        self.connect("realize", self.make_click_through)
        image = Image.new("RGBA", (HIVE_WIDTH, HIVE_HEIGHT), (0, 0, 0, 0))
        draw = ImageDraw.Draw(image, "RGBA")
        draw.line((5, 18, 105, 5), fill=(91, 58, 29, 245), width=8)
        draw.line((72, 11, 62, 31), fill=(116, 78, 36, 255), width=3)
        draw.ellipse((19, 24, 101, 112), fill=(229, 168, 45, 255), outline=(112, 72, 24, 255), width=3)
        for y, inset in ((39, 13), (54, 7), (69, 4), (84, 7), (99, 14)):
            draw.arc((19+inset, y-12, 101-inset, y+12), 5, 175, fill=(153, 99, 25, 230), width=2)
        draw.ellipse((45, 70, 75, 96), fill=(54, 37, 23, 255), outline=(102, 62, 19, 255), width=2)
        self.add(Gtk.Image.new_from_pixbuf(image_to_pixbuf(image)))
        self.move(int(center_x - HIVE_WIDTH / 2), int(center_y - HIVE_HEIGHT / 2))
        self.show_all()

    def make_click_through(self, *_args):
        window = self.get_window()
        if window:
            window.set_pass_through(True)


class DesktopFly(Gtk.Window):
    def __init__(self, vision_enabled: bool = True, fps: int = 30):
        super().__init__(type=Gtk.WindowType.TOPLEVEL)
        self.set_title("FlyLab Desktop Fly")
        # Square transparent canvas prevents held props from being clipped when
        # the fly rotates through diagonal headings.
        self.set_default_size(SPRITE_SIZE, SPRITE_SIZE)
        self.set_size_request(SPRITE_SIZE, SPRITE_SIZE)
        self.set_decorated(False)
        self.set_keep_above(True)
        self.set_skip_taskbar_hint(True)
        self.set_skip_pager_hint(True)
        self.set_accept_focus(False)
        self.set_app_paintable(True)
        screen = self.get_screen()
        visual = screen.get_rgba_visual()
        if visual:
            self.set_visual(visual)
        self.connect("realize", self.make_click_through)
        self.connect("destroy", Gtk.main_quit)
        self.image_widget = Gtk.Image()
        self.add(self.image_widget)

        monitor = screen.get_primary_monitor()
        geometry = screen.get_monitor_geometry(monitor)
        self.bounds = (geometry.x, geometry.y, geometry.width, geometry.height)
        self.hive_x = geometry.x + geometry.width - 85
        self.hive_y = geometry.y + geometry.height * 0.56
        self.hive = HiveWindow(self.hive_x, self.hive_y)
        self.quest = FlyQuest(self.bounds)
        self.inside_hive_until = 0.0
        self.inside_outhouse_until = 0.0
        self.hive_attraction_after = 0.0
        self.previous_appearance = None
        self.quest_left_item = "none"
        self.quest_right_item = "none"
        self.fun_fly = fitted_asset("fly-fun.png", (86, 64))
        self.x = geometry.x + geometry.width * 0.48
        self.y = geometry.y + geometry.height * 0.35
        self.heading = random.random() * math.tau
        self.wing_phase = 0.0
        self.brain = TinyBrain()
        self.vision = LocalVision(ROOT / "stimuli.json") if vision_enabled else None
        self.features = [0.0] * 6
        self.next_vision_at = 0.0
        self.last_tick = time.monotonic()
        self.settings = load_settings()
        self.next_settings_at = 0.0
        self.frame_ms = max(20, int(1000 / max(10, min(50, fps))))
        self.show_all()
        GLib.timeout_add(self.frame_ms, self.tick)

    def make_click_through(self, *_args) -> None:
        window = self.get_window()
        if window:
            window.set_pass_through(True)

    def tick(self) -> bool:
        now = time.monotonic()
        dt = min(0.1, now - self.last_tick)
        self.last_tick = now
        if now >= self.next_settings_at:
            self.settings = load_settings()
            self.next_settings_at = now + 0.5
        appearance = self.settings.get("appearance", "fly")
        if appearance != self.previous_appearance:
            self.quest.set_active(appearance == "fly")
            if appearance == "bee":
                self.hive.show_all()
            else:
                self.hive.hide()
            if appearance == "fly":
                self.quest_left_item = "none"
                self.quest_right_item = "none"
            self.previous_appearance = appearance
        is_bee = appearance == "bee"
        if self.inside_outhouse_until:
            if appearance == "fly" and now < self.inside_outhouse_until:
                return True
            self.inside_outhouse_until = 0.0
            exit_position = self.quest.objects["outhouse"].center
            self.quest.reset()
            self.quest_left_item = "none"
            self.quest_right_item = "none"
            self.x, self.y = exit_position
            self.heading = random.random() * math.tau
            self.show_all()
        if self.inside_hive_until:
            if is_bee and now < self.inside_hive_until:
                return True
            self.inside_hive_until = 0.0
            self.x, self.y = self.hive_x - 48, self.hive_y
            self.heading = math.pi
            self.hive_attraction_after = now + 10.0
            self.show_all()
        if self.vision and now >= self.next_vision_at:
            self.features = self.vision.sample(int(self.x), int(self.y))
            # Slow down screen capture drastically when the desktop is static.
            self.next_vision_at = now + (0.20 if self.vision.last_activity > 0.012 else 0.75)

        left, right = self.brain.step(self.features)
        sensory_turn = self.features[0] * 0.7 + self.features[3] * 1.5
        self.heading += (right - left) * dt * 1.8 + sensory_turn * dt + random.uniform(-0.08, 0.08) * dt
        if is_bee and now >= self.hive_attraction_after:
            desired = math.atan2(self.hive_y - self.y, self.hive_x - self.x)
            angle_error = math.atan2(math.sin(desired - self.heading), math.cos(desired - self.heading))
            self.heading += angle_error * dt * 0.55
        quest_target = self.quest.target_position if appearance == "fly" else None
        if quest_target:
            desired = math.atan2(quest_target[1] - self.y, quest_target[0] - self.x)
            angle_error = math.atan2(math.sin(desired - self.heading), math.cos(desired - self.heading))
            self.heading += angle_error * dt * 1.15
        arousal = 0.55 + self.brain.hormones["octopamine"] / 180
        speed_multiplier = max(0.25, min(3.0, float(self.settings.get("speed_multiplier", 1.0))))
        speed = (24 + arousal * 24) * speed_multiplier * dt
        self.x += math.cos(self.heading) * speed
        self.y += math.sin(self.heading) * speed
        bx, by, bw, bh = self.bounds
        if self.x < bx + 25 or self.x > bx + bw - 25:
            self.heading = math.pi - self.heading
            self.x = min(bx + bw - 25, max(bx + 25, self.x))
        if self.y < by + 25 or self.y > by + bh - 25:
            self.heading = -self.heading
            self.y = min(by + bh - 25, max(by + 25, self.y))
        self.brain.tick_body(dt)
        self.wing_phase += dt * (28 + arousal * 20)
        if (is_bee and now >= self.hive_attraction_after
                and math.hypot(self.hive_x - self.x, self.hive_y - self.y) < 34):
            self.brain.reward(0.4)
            self.brain.apply_effects({"octopamine": 5.0})
            self.inside_hive_until = now + 2.5
            self.hide()
            return True
        if quest_target and math.hypot(quest_target[0] - self.x, quest_target[1] - self.y) < 46:
            collected = self.quest.collect_target()
            if collected == "coffee":
                self.quest_left_item = "coffee"
                self.brain.apply_effects({"caffeine": 25.0, "dopamine": 10.0})
            elif collected == "cigarette":
                self.quest_right_item = "cigarette"
                self.brain.apply_effects({"octopamine": 8.0, "stress": 5.0})
            elif collected == "outhouse":
                self.inside_outhouse_until = now + 180.0
                self.hide()
                return True
        self.move(int(self.x - SPRITE_HALF), int(self.y - SPRITE_HALF))
        self.render_fly()
        return True

    def render_fly(self) -> None:
        base = Image.new("RGBA", (86, 64), (0, 0, 0, 0))
        draw = ImageDraw.Draw(base, "RGBA")
        flap = int(math.sin(self.wing_phase) * 4)
        if self.settings.get("appearance", "fly") == "fly":
            base.alpha_composite(self.fun_fly)
        else:
            draw_appearance(draw, self.settings.get("appearance", "fly"), flap)

        # Items are independent of appearance and do not change the fly brain.
        if self.settings.get("appearance", "fly") == "fly":
            left_item, right_item = self.quest_left_item, self.quest_right_item
        else:
            left_item = self.settings.get("left_item", "none")
            right_item = self.settings.get("right_item", "none")
        draw_held_item(base, left_item, "left")
        draw_held_item(base, right_item, "right")
        # The base sprite is drawn with its head pointing left, while heading=0
        # means movement to the right. Rotate it by 180° so nose and velocity agree.
        base = base.resize((116, 86), Image.Resampling.LANCZOS)
        sprite = Image.new("RGBA", (SPRITE_SIZE, SPRITE_SIZE), (0, 0, 0, 0))
        sprite.alpha_composite(base, ((SPRITE_SIZE - 116) // 2, (SPRITE_SIZE - 86) // 2))
        sprite = sprite.rotate(180 - math.degrees(self.heading), resample=Image.Resampling.BICUBIC)
        self.image_widget.set_from_pixbuf(image_to_pixbuf(sprite))


def main() -> None:
    parser = argparse.ArgumentParser(description="Lightweight FlyLab desktop fly")
    parser.add_argument("--no-vision", action="store_true", help="disable screen capture")
    parser.add_argument("--fps", type=int, default=30, help="animation FPS (10–50)")
    args = parser.parse_args()
    pid_file = Path(os.environ.get("XDG_RUNTIME_DIR", "/tmp")) / "flylab-desktop-fly.pid"
    pid_file.write_text(str(os.getpid()))
    try:
        DesktopFly(vision_enabled=not args.no_vision, fps=args.fps)
        Gtk.main()
    finally:
        try:
            if pid_file.read_text().strip() == str(os.getpid()):
                pid_file.unlink()
        except OSError:
            pass


if __name__ == "__main__":
    main()
