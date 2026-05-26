BASE_RESOLUTION = (960, 540)

AVAILABLE_RESOLUTIONS = [
    (640, 360),
    (960, 540),
    (1280, 720),
    (1600, 900),
    (1920, 1080),
]

COLORS = {
    "canvas_bg": "#1a1a1a",
    "back_button_bg": "#333333",
    "back_button_fg": "#000000",
    "tower_fill": "#4a90e2",
    "tower_outline": "#357abd",
    "tower_text": "#ffffff",
    "enemy_fill": "#e74c3c",
    "enemy_outline": "#c0392b",
    "enemy_hp_bg": "#555555",
    "enemy_hp_fg": "#2ecc71",
    "projectile_fill": "#f1c40f",
    "game_over_text": "#ff3333",
}

GAME_CONFIG = {
    "fps": 60,
    "frame_time_ms": 16,
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
