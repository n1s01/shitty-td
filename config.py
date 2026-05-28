BASE_RESOLUTION = (960, 540)

AVAILABLE_RESOLUTIONS = [
    (640, 360),
    (960, 540),
    (1280, 720),
    (1600, 900),
    (1920, 1080),
]

COLORS = {
    "bg": (26, 26, 26),
    "tower_fill": (74, 144, 226),
    "tower_outline": (53, 122, 189),
    "tower_text": (255, 255, 255),
    "enemy_fill": (231, 76, 60),
    "enemy_outline": (192, 57, 43),
    "enemy_hp_bg": (85, 85, 85),
    "enemy_hp_fg": (46, 204, 113),
    "projectile_fill": (241, 196, 15),
    "game_over_text": (255, 51, 51),
    "button_bg": (51, 51, 51),
    "button_hover": (80, 80, 80),
    "button_text": (255, 255, 255),
    "title_text": (255, 255, 255),
}

GAME_CONFIG = {
    "fps": 60,
    "tower_size": 50,
    "tower_max_hp": 100,
    "enemy_spawn_delay": 90,
    "enemy_size": 20,
    "enemy_max_hp": 2,
    "enemy_speed": 1.5,
    "enemy_damage": 10,
    "projectile_speed": 8,
    "projectile_size": 4,
}

SETTINGS_FILE = "data/settings.json"
