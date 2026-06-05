from config import GAME_CONFIG


def make_wave(wave_index):
    """Считает параметры волны для бесконечного режима.

    wave_index — номер волны, начиная с 0. Чем больше номер, тем сложнее волна:
    врагов больше, они появляются чаще, у них выше HP, скорость и урон.

    Возвращает словарь с ключами:
        count          — сколько врагов в волне
        interval       — задержка между спавнами (в кадрах)
        ranged_every   — каждый N-й враг дальнобойный (0 = нет дальнобойных)
        enemy_hp       — здоровье врага
        enemy_speed    — скорость врага
        enemy_damage   — урон врага
    """
    cfg = GAME_CONFIG["endless"]
    n = wave_index

    count = cfg["base_count"] + cfg["count_growth"] * n

    interval = max(
        cfg["min_interval"],
        cfg["base_interval"] - cfg["interval_decay"] * n,
    )

    enemy_hp = cfg["base_hp"] + n // cfg["hp_growth_every"]

    enemy_speed = cfg["base_speed"]

    enemy_damage = cfg["base_damage"] + cfg["damage_step"] * (
        n // cfg["damage_growth_every"]
    )

    if n < cfg["ranged_start_wave"]:
        ranged_every = 0
    else:
        tighten = n // cfg["ranged_tighten_every"]
        ranged_every = max(cfg["ranged_every_min"], cfg["ranged_every_base"] - tighten)

    return {
        "count": count,
        "interval": interval,
        "ranged_every": ranged_every,
        "enemy_hp": enemy_hp,
        "enemy_speed": enemy_speed,
        "enemy_damage": enemy_damage,
    }
