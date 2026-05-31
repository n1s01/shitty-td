from pygame import _freetype  # type: ignore[attr-defined]


def make_font(size):
    _freetype.init()
    return _freetype.Font(None, size)
