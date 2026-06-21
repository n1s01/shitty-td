"""Загрузка и кэширование изображений игры."""

from pathlib import Path

import pygame

ASSET_ROOT = Path(__file__).resolve().parents[1] / "assets"
TRANSPARENT_MATTE = (70, 124, 58, 0)


class AssetStore:
    """Кеш для изображений. Загрузка и обращение по хешу."""

    def __init__(self):
        """Создаёт пустой кэш изображений."""
        self._images = {}

    def image(self, rel_path, size=None):
        """Возвращает изображение по пути, кэшируя результат.

        Args:
            rel_path: путь к файлу относительно папки assets.
            size: кортеж (width, height) для масштабирования или None.

        Returns:
            Поверхность pygame с загруженным изображением.
        """
        key = (rel_path, size)
        if key not in self._images:
            path = ASSET_ROOT / rel_path
            img = _load_png_surface(path)
            if size:
                img = pygame.transform.scale(img, size)
            self._images[key] = img
        return self._images[key]

    def optional_image(self, rel_path, size=None):
        """Возвращает изображение или None, если его не удалось загрузить.

        Args:
            rel_path: путь к файлу относительно папки assets.
            size: кортеж (width, height) для масштабирования или None.

        Returns:
            Поверхность pygame или None при ошибке загрузки.
        """
        try:
            return self.image(rel_path, size)
        except (FileNotFoundError, ImportError, OSError, pygame.error):
            return None


def _load_png_surface(path):
    """Загружает PNG и подменяет прозрачным пикселям цвет фона.

    Подмена убирает тёмную кайму вокруг полупрозрачных краёв при
    масштабировании.

    Args:
        path: путь к PNG-файлу.

    Returns:
        Поверхность pygame с альфа-каналом.
    """
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
