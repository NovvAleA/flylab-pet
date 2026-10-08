"""Low-rate local screen vision. Only a small ring around the fly is sampled."""

from __future__ import annotations

import json
import math
from pathlib import Path

from PIL import Image, ImageChops, ImageGrab, ImageStat


class LocalVision:
    def __init__(self, config_path: Path, radius: int = 110):
        self.radius = radius
        self.stimuli = json.loads(config_path.read_text(encoding="utf-8"))
        self.previous: Image.Image | None = None
        self.last_activity = 1.0
        self.best_stimulus: str | None = None

    def sample(self, center_x: int, center_y: int) -> list[float]:
        r = self.radius
        try:
            frame = ImageGrab.grab((center_x - r, center_y - r, center_x + r, center_y + r)).convert("RGB").resize((48, 48))
        except Exception:
            return [0.0] * 6

        # Ignore the overlay itself: the fly occupies the center of the captured patch.
        pixels = frame.load()
        for y in range(17, 31):
            for x in range(15, 33):
                pixels[x, y] = (0, 0, 0)

        gray = frame.convert("L")
        left = ImageStat.Stat(gray.crop((0, 0, 24, 48))).mean[0] / 255
        right = ImageStat.Stat(gray.crop((24, 0, 48, 48))).mean[0] / 255
        top = ImageStat.Stat(gray.crop((0, 0, 48, 24))).mean[0] / 255
        bottom = ImageStat.Stat(gray.crop((0, 24, 48, 48))).mean[0] / 255
        motion = 0.0 if self.previous is None else ImageStat.Stat(ImageChops.difference(gray, self.previous)).mean[0] / 255
        self.previous = gray
        self.last_activity = motion

        attraction_x = attraction_y = strongest = 0.0
        self.best_stimulus = None
        for name, definition in self.stimuli.items():
            target = definition["target_rgb"]
            tolerance = definition["tolerance"]
            weight = definition["attraction"]
            sx = sy = count = 0.0
            for y in range(48):
                for x in range(48):
                    red, green, blue = frame.getpixel((x, y))
                    distance = math.sqrt((red-target[0])**2 + (green-target[1])**2 + (blue-target[2])**2)
                    if distance < tolerance:
                        sx += (x - 23.5) / 24
                        sy += (y - 23.5) / 24
                        count += 1
            score = count / (48 * 48) * weight
            if score > strongest:
                strongest, self.best_stimulus = score, name
                attraction_x = sx / max(1, count)
                attraction_y = sy / max(1, count)

        # A few coincidental pixels (for example gray UI text) are not an object.
        if strongest < 0.004:
            strongest = attraction_x = attraction_y = 0.0
            self.best_stimulus = None

        return [right-left, bottom-top, motion, attraction_x, attraction_y, min(1.0, strongest * 20)]
