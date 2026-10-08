"""Reusable desktop-object scene and the first scripted pet quest."""

from __future__ import annotations

import random
from pathlib import Path

import gi
gi.require_version("Gtk", "3.0")
gi.require_version("GdkPixbuf", "2.0")
from gi.repository import GdkPixbuf, GLib, Gtk  # noqa: E402
from PIL import Image, ImageDraw


ASSETS = Path(__file__).resolve().parent / "assets"


def pixbuf(image: Image.Image) -> GdkPixbuf.Pixbuf:
    width, height = image.size
    return GdkPixbuf.Pixbuf.new_from_bytes(
        GLib.Bytes.new(image.tobytes()), GdkPixbuf.Colorspace.RGB,
        True, 8, width, height, width * 4,
    )


def fitted_asset(name: str, size: tuple[int, int]) -> Image.Image:
    source = Image.open(ASSETS / name).convert("RGBA")
    source.thumbnail(size, Image.Resampling.LANCZOS)
    canvas = Image.new("RGBA", size, (0, 0, 0, 0))
    canvas.alpha_composite(source, ((size[0] - source.width) // 2, (size[1] - source.height) // 2))
    return canvas


class DesktopObject(Gtk.Window):
    def __init__(self, asset: str | Image.Image, size: tuple[int, int], title: str):
        super().__init__(type=Gtk.WindowType.TOPLEVEL)
        self.width, self.height = size
        self.center = (0.0, 0.0)
        self.set_title(title)
        self.set_default_size(*size)
        self.set_size_request(*size)
        self.set_decorated(False)
        self.set_keep_above(True)
        self.set_skip_taskbar_hint(True)
        self.set_skip_pager_hint(True)
        self.set_accept_focus(False)
        self.set_app_paintable(True)
        visual = self.get_screen().get_rgba_visual()
        if visual:
            self.set_visual(visual)
        self.connect("realize", self._click_through)
        picture = fitted_asset(asset, size) if isinstance(asset, str) else asset
        self.add(Gtk.Image.new_from_pixbuf(pixbuf(picture)))

    def _click_through(self, *_args):
        window = self.get_window()
        if window:
            window.set_pass_through(True)

    def place(self, x: float, y: float):
        self.center = (x, y)
        self.move(int(x - self.width / 2), int(y - self.height / 2))


class FlyQuest:
    """coffee -> cigarette -> outhouse; more steps can be registered later."""

    ORDER = ("coffee", "cigarette", "outhouse")

    def __init__(self, bounds: tuple[int, int, int, int]):
        self.bounds = bounds
        self.objects = {
            "coffee": DesktopObject("coffee.png", (126, 126), "FlyLab Coffee"),
            "cigarette": DesktopObject("cigarette.png", (136, 136), "FlyLab Cigarette"),
            "outhouse": DesktopObject("outhouse.png", (178, 178), "FlyLab Outhouse"),
        }
        smoke_image = Image.new("RGBA", (110, 100), (0, 0, 0, 0))
        smoke = ImageDraw.Draw(smoke_image, "RGBA")
        smoke.ellipse((44, 58, 77, 89), fill=(116, 108, 105, 165), outline=(62, 57, 55, 190), width=2)
        smoke.ellipse((24, 35, 61, 70), fill=(142, 134, 131, 145), outline=(62, 57, 55, 180), width=2)
        smoke.ellipse((51, 21, 91, 58), fill=(156, 149, 146, 125), outline=(62, 57, 55, 165), width=2)
        smoke.ellipse((35, 4, 67, 34), fill=(176, 170, 168, 105), outline=(62, 57, 55, 145), width=2)
        self.smoke = DesktopObject(smoke_image, smoke_image.size, "FlyLab Outhouse Smoke")
        self.step = 0
        self.active = False
        self.outhouse_occupied = False
        self.reset()

    @property
    def target_name(self) -> str | None:
        return self.ORDER[self.step] if self.active and self.step < len(self.ORDER) else None

    @property
    def target_position(self) -> tuple[float, float] | None:
        name = self.target_name
        return self.objects[name].center if name else None

    def reset(self):
        bx, by, bw, bh = self.bounds
        positions: list[tuple[float, float]] = []
        for name in self.ORDER:
            for _ in range(100):
                point = (random.uniform(bx + 130, bx + bw - 130), random.uniform(by + 130, by + bh - 130))
                if all((point[0]-x)**2 + (point[1]-y)**2 > 280**2 for x, y in positions):
                    break
            positions.append(point)
            self.objects[name].place(*point)
        toilet_x, toilet_y = self.objects["outhouse"].center
        self.smoke.place(toilet_x + 12, toilet_y - 118)
        self.step = 0
        self.outhouse_occupied = False
        self._refresh()

    def set_active(self, active: bool):
        if active and not self.active:
            self.active = True
            self.reset()
        elif not active:
            self.active = False
            self._refresh()

    def collect_target(self) -> str | None:
        name = self.target_name
        if name is None:
            return None
        self.step += 1
        if name == "outhouse":
            self.outhouse_occupied = True
        self._refresh()
        return name

    def _refresh(self):
        for index, name in enumerate(self.ORDER):
            visible = self.active and (index >= self.step or (name == "outhouse" and self.outhouse_occupied))
            if visible:
                self.objects[name].show_all()
            else:
                self.objects[name].hide()
        if self.active and self.outhouse_occupied:
            self.smoke.show_all()
        else:
            self.smoke.hide()
