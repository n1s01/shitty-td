from pathlib import Path

import pygame
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
ASSET_ROOT = ROOT / "assets"


def surface(size):
    return pygame.Surface(size, pygame.SRCALPHA)


TRANSPARENT_MATTE = (70, 124, 58, 0)


def save(surf, path):
    path.parent.mkdir(parents=True, exist_ok=True)
    raw = pygame.image.tobytes(surf, "RGBA")
    img = Image.frombytes("RGBA", surf.get_size(), raw)
    pixels = [TRANSPARENT_MATTE if pixel[3] == 0 else pixel for pixel in img.getdata()]
    img.putdata(pixels)
    img.save(path)


def px(surf, color, rect):
    pygame.draw.rect(surf, color, rect)


def outline_rect(surf, color, rect, width=1):
    pygame.draw.rect(surf, color, rect, width)


# Палитра травы: от тёмной (в тени) до светлой (на солнце)
GRASS_SHADES = [
    (60, 108, 46),  # 0 — самая тёмная, ложбинки
    (68, 118, 52),  # 1
    (76, 128, 58),  # 2 — основной средний тон
    (84, 138, 64),  # 3
    (94, 150, 72),  # 4 — светлые проплешины на солнце
]


def _hash(x, y, seed):
    """Детерминированный шум — чтобы текстура воспроизводилась при перегенерации."""
    h = (x * 374761393 + y * 668265263 + seed * 2654435761) & 0xFFFFFFFF
    h ^= h >> 15
    h = (h * 2246822519) & 0xFFFFFFFF
    h ^= h >> 13
    return h & 0xFFFFFFFF


def _shade_index(value):
    """Распределяем 0..99 по оттенкам так, чтобы средний тон преобладал."""
    if value < 8:
        return 0
    if value < 30:
        return 1
    if value < 72:
        return 2
    if value < 92:
        return 3
    return 4


def _grass_base(img, seed):
    """Мягкая пятнистая основа: крупные клочки + мелкая зернистость."""
    w, h = img.get_size()
    for by in range(0, h, 2):
        for bx in range(0, w, 2):
            coarse = _hash(bx // 8, by // 8, seed) % 100  # крупные пятна
            fine = _hash(bx, by, seed + 7) % 100  # мелкая зернистость
            value = (coarse * 7 + fine * 3) // 10
            px(img, GRASS_SHADES[_shade_index(value)], (bx, by, 2, 2))

    # редкие точечные блики и тёмные крапинки для живости
    for n in range(10):
        hx = _hash(n, seed, 101) % w
        hy = _hash(n, seed, 202) % h
        spec = _hash(n, seed, 303) % 5
        if spec == 0:
            px(img, GRASS_SHADES[4], (hx, hy, 1, 1))
        elif spec == 1:
            px(img, GRASS_SHADES[0], (hx, hy, 1, 1))


def _blade(img, x, base_y, height, lean=0):
    tip = (118, 182, 88)
    light = (96, 156, 74)
    mid = (78, 134, 60)
    base_c = (52, 100, 44)
    for h in range(height):
        y = base_y - h
        bx = x + (lean if h >= height - 1 else 0)
        if h == 0:
            c = base_c
        elif h == height - 1:
            c = tip
        elif h >= height - 2:
            c = light
        else:
            c = mid
        px(img, c, (bx, y, 1, 1))
        # тонкая тень у основания слева — объём
        if 0 < h < height - 1 and bx - 1 >= 0:
            px(img, base_c, (bx - 1, y, 1, 1))


def make_grass(variant=0):
    img = surface((32, 32))
    _grass_base(img, seed=variant + 1)

    # лезвия распределены по всей высоте тайла, чтобы при замостке
    # не появлялись горизонтальные полосы
    if variant == 0:
        # прямые лезвия средней высоты
        for x, y, h in [
            (5, 12, 5),
            (11, 8, 4),
            (18, 27, 5),
            (24, 15, 4),
            (28, 23, 6),
            (3, 21, 3),
            (14, 30, 5),
            (21, 11, 4),
            (8, 29, 4),
            (26, 6, 5),
            (2, 17, 3),
            (16, 5, 4),
        ]:
            _blade(img, x, y, h)
    elif variant == 1:
        # лезвия наклонены вправо — ветер
        for x, y, h in [
            (4, 26, 5),
            (10, 9, 5),
            (16, 18, 4),
            (22, 30, 5),
            (27, 13, 6),
            (8, 21, 4),
            (19, 7, 5),
            (13, 30, 5),
            (25, 24, 4),
            (6, 6, 4),
            (30, 17, 5),
        ]:
            _blade(img, x, y, h, lean=1)
    elif variant == 2:
        # короткая густая трава
        for x, y, h in [
            (3, 27, 3),
            (7, 12, 3),
            (11, 20, 2),
            (15, 8, 3),
            (19, 27, 3),
            (23, 16, 2),
            (27, 7, 3),
            (5, 23, 2),
            (13, 24, 3),
            (21, 30, 2),
            (29, 24, 3),
            (9, 30, 2),
            (17, 13, 3),
            (25, 6, 3),
        ]:
            _blade(img, x, y, h)
    else:
        # высокая трава, некоторые лезвия наклонены
        for x, y, h, lean in [
            (5, 12, 7, 0),
            (9, 25, 6, 1),
            (14, 8, 7, -1),
            (19, 24, 8, 0),
            (24, 15, 6, 1),
            (28, 30, 7, -1),
            (3, 22, 4, 0),
            (17, 30, 5, 1),
            (11, 6, 6, 0),
            (22, 9, 5, -1),
            (7, 18, 5, 1),
        ]:
            _blade(img, x, y, h, lean)

    return img


def make_grass_tuft(variant):
    img = surface((18, 18))
    dark = (42, 94, 45)
    mid = (73, 142, 62)
    light = (111, 172, 78)
    blades = [
        (8, 14, 2, 5, mid),
        (5, 12, 2, 7, dark),
        (11, 11, 2, 8, light),
        (14, 13, 2, 5, mid),
    ]
    if variant:
        blades.extend([(3, 14, 2, 4, light), (9, 9, 2, 9, dark)])
    for x, y, w, h, color in blades:
        px(img, color, (x, y - h, w, h))
    px(img, (48, 105, 45), (4, 14, 11, 2))
    return img


def make_clover():
    img = surface((18, 18))
    stem = (50, 111, 48)
    leaf = (70, 156, 69)
    shine = (116, 196, 91)
    px(img, stem, (8, 8, 2, 7))
    for rect in [(5, 6, 4, 4), (10, 6, 4, 4), (7, 3, 4, 4), (8, 9, 4, 4)]:
        px(img, leaf, rect)
    px(img, shine, (7, 4, 2, 1))
    return img


def make_flowers(color):
    img = surface((18, 18))
    stem = (48, 109, 48)
    center = (238, 196, 84)
    for base_x, base_y in [(5, 12), (12, 14), (9, 9)]:
        px(img, stem, (base_x, base_y - 4, 1, 5))
        px(img, color, (base_x - 1, base_y - 6, 3, 3))
        px(img, center, (base_x, base_y - 5, 1, 1))
    return img


def make_dirt():
    img = surface((32, 32))
    img.fill((121, 86, 50))
    for color, rect in [
        ((151, 108, 61), (0, 6, 8, 3)),
        ((91, 64, 42), (10, 2, 5, 2)),
        ((164, 120, 69), (18, 14, 10, 3)),
        ((86, 58, 38), (3, 24, 8, 2)),
        ((141, 99, 56), (25, 26, 5, 3)),
    ]:
        px(img, color, rect)
    return img


def make_planks():
    img = surface((32, 32))
    img.fill((116, 72, 39))
    for y in (7, 15, 23):
        px(img, (73, 43, 28), (0, y, 32, 2))
    for x in (9, 20):
        px(img, (92, 54, 31), (x, 0, 2, 32))
    for rect in [(5, 3, 2, 2), (24, 11, 2, 2), (13, 27, 2, 2)]:
        px(img, (176, 119, 62), rect)
    return img


def make_tilled_soil():
    img = surface((32, 32))
    img.fill((81, 50, 31))
    for y in (4, 11, 18, 25):
        px(img, (52, 34, 24), (0, y, 10, 2))
        px(img, (52, 34, 24), (14, y + 1, 18, 2))
        px(img, (112, 70, 38), (3, y + 3, 9, 1))
        px(img, (112, 70, 38), (18, y + 4, 10, 1))
    for rect in [
        (5, 2, 3, 2),
        (17, 6, 2, 2),
        (26, 9, 3, 2),
        (9, 15, 3, 2),
        (22, 21, 4, 2),
        (3, 28, 2, 2),
        (15, 30, 3, 1),
    ]:
        px(img, (133, 82, 43), rect)
    for rect in [(12, 7, 2, 2), (28, 17, 2, 2), (6, 22, 2, 2)]:
        px(img, (46, 31, 22), rect)
    return img


def make_tower():
    img = surface((64, 64))
    px(img, (72, 44, 29), (19, 26, 28, 29))
    px(img, (106, 63, 36), (22, 29, 22, 25))
    px(img, (158, 91, 45), (15, 19, 34, 10))
    px(img, (101, 54, 33), (12, 25, 40, 5))
    px(img, (64, 39, 28), (20, 16, 24, 5))
    px(img, (200, 139, 61), (27, 37, 10, 18))
    px(img, (55, 35, 25), (31, 45, 2, 10))
    px(img, (239, 198, 95), (38, 32, 5, 5))
    px(img, (239, 198, 95), (22, 32, 5, 5))
    px(img, (93, 56, 35), (7, 39, 14, 7))
    px(img, (225, 171, 78), (9, 41, 10, 3))
    px(img, (45, 27, 20), (13, 46, 2, 5))
    outline_rect(img, (42, 25, 20), (19, 26, 28, 29), 2)
    outline_rect(img, (58, 31, 24), (12, 25, 40, 5), 1)
    return img


def make_enemy_raider():
    img = surface((32, 32))
    px(img, (57, 89, 53), (10, 7, 13, 12))
    px(img, (69, 114, 63), (8, 11, 17, 10))
    px(img, (92, 57, 38), (9, 20, 15, 7))
    px(img, (41, 63, 38), (7, 14, 4, 6))
    px(img, (41, 63, 38), (23, 14, 4, 6))
    px(img, (236, 213, 116), (12, 12, 3, 3))
    px(img, (236, 213, 116), (19, 12, 3, 3))
    px(img, (48, 32, 27), (15, 17, 5, 2))
    px(img, (168, 168, 151), (25, 9, 3, 14))
    outline_rect(img, (31, 43, 31), (8, 10, 17, 17), 1)
    return img


def make_enemy_ranged():
    img = surface((32, 32))
    px(img, (58, 45, 82), (9, 6, 15, 18))
    px(img, (83, 59, 113), (7, 12, 19, 13))
    px(img, (42, 34, 59), (11, 10, 11, 7))
    px(img, (222, 171, 86), (14, 15, 5, 3))
    px(img, (123, 78, 44), (4, 18, 22, 3))
    px(img, (207, 181, 95), (24, 16, 2, 7))
    outline_rect(img, (35, 27, 50), (7, 12, 19, 13), 1)
    return img


def make_wave_button():
    w, h = 120, 36
    img = surface((w, h))
    # основа — тёмное дерево
    img.fill((88, 52, 28))
    # светлая середина доски
    px(img, (118, 72, 39), (3, 3, w - 6, h - 6))
    # горизонтальные прожилки дерева
    for y in (8, 14, 20, 26):
        px(img, (104, 63, 34), (5, y, w - 10, 1))
        px(img, (132, 84, 46), (5, y + 1, w - 10, 1))
    # вертикальные гвоздики по краям
    for nail_x in (10, w - 11):
        px(img, (62, 38, 24), (nail_x, 8, 5, 20))
        px(img, (148, 102, 58), (nail_x + 1, 9, 3, 18))
        px(img, (198, 158, 88), (nail_x + 1, 9, 2, 2))
    # тёмная рамка
    outline_rect(img, (52, 29, 14), (0, 0, w, h), 2)
    # внутренняя светлая рамка — объём
    outline_rect(img, (148, 98, 54), (3, 3, w - 6, h - 6), 1)
    return img


def make_arrow():
    img = surface((24, 8))
    px(img, (212, 189, 119), (1, 3, 16, 2))
    px(img, (226, 226, 213), (17, 1, 5, 6))
    px(img, (118, 72, 42), (0, 2, 3, 4))
    return img


def make_firebolt():
    img = surface((18, 18))
    px(img, (255, 94, 35), (5, 4, 8, 10))
    px(img, (255, 177, 48), (7, 6, 6, 7))
    px(img, (255, 229, 110), (9, 8, 3, 4))
    px(img, (168, 49, 39), (3, 7, 3, 5))
    return img


def make_tower_keeper(frame=0):
    img = surface((32, 32))
    skin = (220, 159, 100)
    skin_dark = (141, 84, 58)
    shirt = (66, 112, 147)
    shirt_dark = (35, 61, 91)
    hair = (72, 43, 31)
    belt = (52, 34, 27)
    bow = (99, 62, 36)
    metal = (213, 209, 181)
    flash = (255, 215, 86)

    px(img, shirt_dark, (11, 15, 10, 10))
    px(img, shirt, (12, 14, 10, 10))
    px(img, belt, (11, 22, 12, 2))
    px(img, skin_dark, (11, 8, 12, 10))
    px(img, skin, (12, 7, 12, 9))
    px(img, hair, (11, 5, 13, 5))
    px(img, hair, (10, 8, 3, 5))
    px(img, (38, 29, 27), (14, 12, 2, 2))
    px(img, (38, 29, 27), (20, 12, 2, 2))
    px(img, (118, 63, 45), (16, 16, 5, 1))

    if frame == 0:
        px(img, skin, (7, 16, 5, 3))
        px(img, skin, (21, 16, 5, 3))
        px(img, bow, (4, 18, 22, 2))
        px(img, metal, (25, 16, 4, 6))
    elif frame == 1:
        px(img, skin, (7, 14, 6, 3))
        px(img, skin, (21, 15, 6, 3))
        px(img, bow, (4, 15, 23, 2))
        px(img, metal, (26, 13, 4, 6))
        px(img, (235, 235, 207), (2, 14, 5, 1))
    else:
        px(img, skin, (6, 13, 7, 3))
        px(img, skin, (21, 14, 7, 3))
        px(img, bow, (3, 14, 24, 2))
        px(img, metal, (26, 11, 4, 6))
        px(img, flash, (29, 12, 3, 2))
        px(img, (255, 244, 161), (30, 10, 2, 6))

    px(img, shirt_dark, (12, 25, 3, 5))
    px(img, shirt_dark, (19, 25, 3, 5))
    return img


def make_pond(w, h, variant):
    img = surface((w, h))
    color_sets = [
        ((37, 111, 135), (54, 151, 162), (125, 205, 196)),
        ((34, 89, 130), (45, 135, 166), (116, 190, 207)),
    ]
    dark, mid, light = color_sets[variant % len(color_sets)]
    px(img, dark, (9, 10, w - 18, h - 18))
    px(img, dark, (15, 5, w - 30, h - 8))
    px(img, mid, (14, 13, w - 28, h - 24))
    px(img, mid, (22, 8, w - 36, h - 16))
    px(img, light, (22, 14, 12, 3))
    px(img, light, (w - 30, h - 18, 9, 2))
    for rect in [(5, 22, 5, 4), (w - 13, 17, 5, 4), (18, h - 8, 7, 3)]:
        px(img, (61, 103, 48), rect)
    return img


def make_log(w, h, variant):
    img = surface((w, h))
    base = (103, 62, 35) if variant == 0 else (124, 78, 43)
    px(img, (61, 39, 28), (8, 10, w - 15, h - 14))
    px(img, base, (10, 8, w - 20, h - 12))
    px(img, (161, 105, 56), (14, 10, w - 30, 4))
    px(img, (70, 43, 30), (18, h - 12, w - 36, 3))
    px(img, (181, 130, 71), (w - 16, 11, 8, 8))
    px(img, (75, 49, 34), (w - 14, 13, 4, 4))
    if variant:
        px(img, (70, 43, 30), (22, 4, 4, 9))
        px(img, (70, 43, 30), (30, h - 10, 5, 7))
    return img


def make_branch(w, h, variant):
    img = surface((w, h))
    px(img, (88, 54, 36), (6, h // 2, w - 12, 4))
    px(img, (127, 82, 47), (10, h // 2 - 1, w - 20, 2))
    if variant == 0:
        px(img, (88, 54, 36), (20, 8, 4, 13))
        px(img, (88, 54, 36), (32, 18, 4, 10))
    else:
        px(img, (88, 54, 36), (14, 15, 11, 3))
        px(img, (88, 54, 36), (29, 6, 4, 14))
        px(img, (88, 54, 36), (38, 18, 8, 3))
    return img


def make_stones():
    img = surface((48, 32))
    for color, rect in [
        ((78, 83, 82), (5, 14, 13, 10)),
        ((112, 119, 114), (18, 8, 15, 14)),
        ((62, 68, 68), (31, 17, 12, 8)),
        ((151, 158, 149), (22, 10, 5, 3)),
        ((101, 108, 103), (8, 16, 5, 3)),
    ]:
        px(img, color, rect)
    return img


def make_stump():
    img = surface((36, 36))
    px(img, (76, 49, 32), (9, 13, 19, 14))
    px(img, (148, 94, 48), (7, 9, 23, 12))
    px(img, (197, 145, 72), (11, 11, 15, 7))
    px(img, (88, 56, 35), (16, 13, 5, 3))
    px(img, (61, 40, 29), (9, 25, 18, 4))
    return img


def main():
    pygame.init()
    assets = {
        "tiles/grass.png": make_grass(0),
        "tiles/grass_1.png": make_grass(0),
        "tiles/grass_2.png": make_grass(1),
        "tiles/grass_3.png": make_grass(2),
        "tiles/grass_4.png": make_grass(3),
        "tiles/dirt.png": make_dirt(),
        "tiles/tavern_planks.png": make_planks(),
        "tiles/tilled_soil.png": make_tilled_soil(),
        "decor/grass_tuft_1.png": make_grass_tuft(0),
        "decor/grass_tuft_2.png": make_grass_tuft(1),
        "decor/clover.png": make_clover(),
        "decor/flowers_blue.png": make_flowers((94, 139, 214)),
        "decor/flowers_yellow.png": make_flowers((228, 207, 79)),
        "sprites/tavern_tower.png": make_tower(),
        "sprites/tower_keeper_idle.png": make_tower_keeper(0),
        "sprites/tower_keeper_shoot_1.png": make_tower_keeper(1),
        "sprites/tower_keeper_shoot_2.png": make_tower_keeper(2),
        "sprites/enemy_raider.png": make_enemy_raider(),
        "sprites/enemy_ranged.png": make_enemy_ranged(),
        "sprites/projectile_arrow.png": make_arrow(),
        "sprites/projectile_firebolt.png": make_firebolt(),
        "obstacles/pond_1.png": make_pond(64, 48, 0),
        "obstacles/pond_2.png": make_pond(72, 48, 1),
        "obstacles/dead_log_1.png": make_log(64, 32, 0),
        "obstacles/dead_log_2.png": make_log(56, 32, 1),
        "obstacles/dry_branch_1.png": make_branch(48, 32, 0),
        "obstacles/dry_branch_2.png": make_branch(56, 32, 1),
        "obstacles/stones_1.png": make_stones(),
        "obstacles/stump_1.png": make_stump(),
        "ui/wave_button.png": make_wave_button(),
    }
    for rel_path, img in assets.items():
        save(img, ASSET_ROOT / rel_path)
    pygame.quit()


if __name__ == "__main__":
    main()
