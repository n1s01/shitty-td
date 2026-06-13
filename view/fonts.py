from pathlib import Path

from pygame import _freetype

PIXEL_FONT_PATH = (
    Path(__file__).resolve().parents[1] / "assets" / "fonts" / "Handjet.ttf"
)


def make_font(size):
    _freetype.init()
    return _freetype.Font(None, size)


def make_ui_font(size):
    _freetype.init()
    if PIXEL_FONT_PATH.exists():
        return _freetype.Font(str(PIXEL_FONT_PATH), size)
    return _freetype.Font(None, size)
