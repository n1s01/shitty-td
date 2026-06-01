from pygame import _freetype


def make_font(size):
    _freetype.init()
    return _freetype.Font(None, size)
