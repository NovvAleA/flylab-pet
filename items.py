"""Drawable item registry. Add a decorated function to introduce a new item."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from PIL import Image, ImageDraw


@dataclass(frozen=True)
class Item:
    key: str
    title: str
    painter: Callable[[ImageDraw.ImageDraw], None] | None


ITEMS: dict[str, Item] = {}


def item(key: str, title: str):
    def register(painter):
        ITEMS[key] = Item(key, title, painter)
        return painter
    return register


ITEMS["none"] = Item("none", "Ничего", None)


@item("coffee", "Кофе")
def coffee(draw):
    draw.polygon(((8, 5), (21, 5), (19, 20), (10, 20)), fill=(229, 218, 190, 255), outline=(103, 73, 46, 255))
    draw.ellipse((8, 3, 21, 8), fill=(244, 235, 211, 255), outline=(103, 73, 46, 255))
    draw.ellipse((10, 4, 19, 7), fill=(73, 38, 19, 255))
    draw.arc((17, 8, 25, 17), -80, 85, fill=(229, 218, 190, 255), width=2)


@item("cigarette", "Сигарета")
def cigarette(draw):
    draw.line((5, 11, 20, 16), fill=(236, 231, 218, 255), width=4)
    draw.line((4, 10, 7, 11), fill=(238, 92, 35, 255), width=4)
    draw.line((18, 15, 21, 16), fill=(194, 139, 60, 255), width=4)
    draw.arc((0, 13, 12, 25), 55, 205, fill=(210, 216, 207, 145), width=1)


@item("sandwich", "Бутерброд")
def sandwich(draw):
    draw.polygon(((5, 6), (23, 10), (8, 22)), fill=(238, 195, 91, 255), outline=(115, 72, 30, 255))
    draw.line((8, 15, 20, 11), fill=(68, 145, 55, 255), width=3)
    draw.line((9, 18, 17, 14), fill=(190, 52, 39, 255), width=2)


@item("helmet", "Шлем")
def helmet(draw):
    draw.pieslice((4, 3, 24, 23), 180, 360, fill=(242, 183, 25, 255), outline=(83, 67, 24, 255))
    draw.rectangle((3, 12, 25, 16), fill=(215, 145, 15, 255), outline=(83, 67, 24, 255))


@item("pink_flower", "Розовый цветочек")
def pink_flower(draw):
    draw.line((18, 14, 7, 25), fill=(54, 143, 62, 255), width=2)
    draw.ellipse((8, 18, 14, 23), fill=(76, 176, 80, 255))
    for bounds in ((3, 2, 12, 12), (11, 2, 20, 12), (2, 9, 12, 18), (12, 9, 22, 18)):
        draw.ellipse(bounds, fill=(244, 103, 176, 255), outline=(178, 47, 116, 255))
    draw.ellipse((8, 7, 16, 15), fill=(255, 213, 55, 255), outline=(171, 112, 20, 255))


@item("kite", "Воздушный змей")
def kite(draw):
    # The fly holds the string; the diamond and bows remain visible at sprite scale.
    draw.arc((8, 10, 34, 36), 155, 285, fill=(91, 74, 55, 255), width=1)
    draw.polygon(((3, 2), (13, 8), (5, 18), (0, 9)), fill=(73, 160, 238, 255), outline=(31, 78, 126, 255))
    draw.line((3, 2, 5, 18), fill=(255, 238, 196, 210), width=1)
    draw.line((0, 9, 13, 8), fill=(255, 238, 196, 210), width=1)
    draw.polygon(((15, 20), (19, 18), (18, 23)), fill=(239, 76, 77, 255))
    draw.polygon(((21, 26), (25, 24), (24, 29)), fill=(255, 184, 44, 255))


@item("ak", "Автомат Калашникова")
def ak(draw):
    draw.line((1, 8, 25, 16), fill=(40, 43, 39, 255), width=4)
    draw.rectangle((10, 11, 21, 17), fill=(95, 57, 25, 255), outline=(35, 29, 22, 255))
    draw.polygon(((13, 16), (20, 18), (17, 25), (12, 22)), fill=(78, 47, 23, 255))
    draw.line((22, 16, 29, 19), fill=(105, 62, 27, 255), width=5)


def draw_held_item(canvas: Image.Image, key: str, side: str) -> None:
    selected = ITEMS.get(key, ITEMS["none"])
    if selected.painter is None:
        return
    layer = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(layer, "RGBA")
    draw.line((31, 26, 17, 14), fill=(142, 91, 34, 235), width=2)
    selected.painter(draw)
    if side == "right":
        layer = layer.transpose(Image.Transpose.FLIP_TOP_BOTTOM)
    canvas.alpha_composite(layer)
