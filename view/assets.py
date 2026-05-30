from pathlib import Path

import pygame


ASSET_ROOT = Path(__file__).resolve().parents[1] / "assets"
TRANSPARENT_MATTE = (70, 124, 58, 0)


class AssetStore:
    def __init__(self):
        self._images = {}

    def image(self, rel_path, size=None):
        key = (rel_path, size)
        if key not in self._images:
            path = ASSET_ROOT / rel_path
            img = _load_png_surface(path)
            if size:
                img = pygame.transform.scale(img, size)
            self._images[key] = img
        return self._images[key]

    def optional_image(self, rel_path, size=None):
        try:
            return self.image(rel_path, size)
        except (FileNotFoundError, ImportError, OSError, pygame.error):
            return None


def _load_png_surface(path):
    from PIL import Image

    with Image.open(path) as source:
        source = source.convert("RGBA")
        pixels = [
            TRANSPARENT_MATTE if pixel[3] == 0 else pixel for pixel in source.getdata()
        ]
        source.putdata(pixels)
        return pygame.image.frombytes(
            source.tobytes(), source.size, "RGBA"
        ).convert_alpha()
