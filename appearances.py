"""Visual appearance registry. It does not affect the fly brain or behavior."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from PIL import ImageDraw


@dataclass(frozen=True)
class Appearance:
    key: str
    title: str
    painter: Callable[[ImageDraw.ImageDraw, int], None]


APPEARANCES: dict[str, Appearance] = {}


def appearance(key: str, title: str):
    def register(painter):
        APPEARANCES[key] = Appearance(key, title, painter)
        return painter
    return register


def wings(draw, flap, tint=(210, 232, 224, 90)):
    outline = (180, 208, 196, 145)
    draw.ellipse((30, 7-flap, 76, 29-flap), fill=tint, outline=outline, width=1)
    draw.ellipse((30, 35+flap, 76, 57+flap), fill=tint, outline=outline, width=1)


def legs(draw):
    for side in (-1, 1):
        for origin_x, reach in ((34, 19), (43, 22), (52, 17)):
            draw.line((origin_x, 32+side*3, origin_x+reach, 32+side*(14+(origin_x % 3)*3)),
                      fill=(96, 62, 27, 230), width=2)


@appearance("fly", "Муха")
def fly(draw, flap):
    wings(draw, flap)
    legs(draw)
    draw.ellipse((27, 22, 65, 42), fill=(83, 49, 18, 255))
    draw.ellipse((17, 23, 36, 41), fill=(125, 78, 26, 255))
    draw.ellipse((14, 24, 21, 31), fill=(188, 34, 22, 255))
    draw.ellipse((14, 34, 21, 41), fill=(188, 34, 22, 255))


@appearance("bee", "Пчела")
def bee(draw, flap):
    wings(draw, flap, (225, 242, 248, 115))
    legs(draw)
    draw.ellipse((25, 21, 68, 43), fill=(242, 181, 28, 255), outline=(74, 50, 19, 255))
    for x in (37, 48, 59):
        draw.rectangle((x, 23, x+5, 41), fill=(55, 43, 27, 255))
    draw.polygon(((68, 27), (78, 32), (68, 37)), fill=(72, 50, 25, 255))
    draw.ellipse((16, 23, 34, 41), fill=(75, 52, 25, 255))
    draw.ellipse((15, 25, 21, 31), fill=(40, 39, 34, 255))
    draw.ellipse((15, 34, 21, 40), fill=(40, 39, 34, 255))
    draw.line((21, 24, 14, 17), fill=(55, 43, 27, 255), width=1)
    draw.line((25, 23, 22, 14), fill=(55, 43, 27, 255), width=1)


@appearance("ladybug", "Божья коровка")
def ladybug(draw, flap):
    # Small translucent underwings keep the flying silhouette readable.
    wings(draw, flap, (225, 238, 228, 70))
    legs(draw)
    draw.ellipse((25, 18, 68, 46), fill=(216, 42, 35, 255), outline=(54, 39, 29, 255), width=2)
    draw.line((47, 20, 47, 44), fill=(45, 34, 28, 255), width=2)
    for x, y in ((34, 26), (38, 37), (56, 26), (57, 38)):
        draw.ellipse((x-3, y-3, x+3, y+3), fill=(37, 32, 28, 255))
    draw.ellipse((16, 23, 33, 41), fill=(38, 34, 29, 255))
    draw.ellipse((15, 26, 20, 31), fill=(245, 238, 211, 255))
    draw.ellipse((15, 34, 20, 39), fill=(245, 238, 211, 255))


def draw_appearance(draw: ImageDraw.ImageDraw, key: str, flap: int) -> None:
    APPEARANCES.get(key, APPEARANCES["fly"]).painter(draw, flap)
