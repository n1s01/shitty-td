BASE_RESOLUTION = (960, 540)

GAME_ZOOM = 2
LOGICAL_RESOLUTION = (BASE_RESOLUTION[0] * GAME_ZOOM, BASE_RESOLUTION[1] * GAME_ZOOM)

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
    "enemy_projectile_fill": (255, 165, 0),
}

GAME_CONFIG = {
    "fps": 60,
    "tower_size": 50,
    "tower_hitbox_size": 170,
    "tower_max_hp": 100,
    "enemy_spawn_delay": 90,
    "enemy_size": 20,
    "enemy_max_hp": 2,
    "enemy_speed": 1.5,
    "enemy_damage": 10,
    "projectile_speed": 8,
    "projectile_size": 4,
    "tower_shoot_anim_frames": 14,
    "ranged_enemy_range": 400,
    "ranged_enemy_fire_rate": 90,
    "ranged_enemy_initial_delay": 75,
    "ranged_enemy_projectile_speed": 4,
    "ranged_enemy_projectile_size": 5,
    "grid_cols": 300,
    "grid_rows": 170,
    "map_obstacle_count": 18,
    "map_obstacles": [
        {"asset": "obstacles/pond_1.png", "size": (64, 48)},
        {"asset": "obstacles/pond_2.png", "size": (72, 48)},
        {"asset": "obstacles/dead_log_1.png", "size": (64, 32)},
        {"asset": "obstacles/dead_log_2.png", "size": (56, 32)},
        {"asset": "obstacles/dry_branch_1.png", "size": (48, 32)},
        {"asset": "obstacles/dry_branch_2.png", "size": (56, 32)},
        {"asset": "obstacles/stones_1.png", "size": (48, 32)},
        {"asset": "obstacles/stump_1.png", "size": (36, 36)},
    ],
    "map_obstacle_safe_radius_factor": 0.18,
    "waves": [
        {"count": 6, "interval": 90, "ranged_every": 0},
        {"count": 9, "interval": 80, "ranged_every": 4},
        {"count": 12, "interval": 70, "ranged_every": 3},
        {"count": 16, "interval": 60, "ranged_every": 3},
        {"count": 20, "interval": 50, "ranged_every": 2},
    ],
    "knockback_force": 4,
    "knockback_decay": 0.75,
    "hit_flash_frames": 10,
}

SETTINGS_FILE = "data/settings.json"
