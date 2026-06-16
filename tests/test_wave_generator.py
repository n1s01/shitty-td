"""Тесты для генератора волн (core/wave_generator.py).

make_wave(n) считает параметры n-й волны бесконечного режима.
С ростом номера волны должно становиться сложнее.
"""

from config import GAME_CONFIG
from core.wave_generator import make_wave

CFG = GAME_CONFIG["endless"]


def test_first_wave_matches_base_config():
    wave = make_wave(0)
    assert wave["count"] == CFG["base_count"]
    assert wave["interval"] == CFG["base_interval"]
    assert wave["enemy_hp"] == CFG["base_hp"]
    assert wave["enemy_speed"] == CFG["base_speed"]
    assert wave["enemy_damage"] == CFG["base_damage"]


def test_enemy_count_grows():
    assert make_wave(5)["count"] > make_wave(0)["count"]
    # Растёт линейно на count_growth за волну.
    assert make_wave(1)["count"] - make_wave(0)["count"] == CFG["count_growth"]


def test_interval_decreases_but_not_below_min():
    # Интервал между спавнами уменьшается с ростом волны...
    assert make_wave(3)["interval"] < make_wave(0)["interval"]
    # ...но никогда не опускается ниже минимума.
    assert make_wave(999)["interval"] == CFG["min_interval"]


def test_enemy_hp_grows_over_time():
    assert make_wave(100)["enemy_hp"] > make_wave(0)["enemy_hp"]
    # HP прибавляется каждые hp_growth_every волн.
    step = CFG["hp_growth_every"]
    assert make_wave(step)["enemy_hp"] == make_wave(0)["enemy_hp"] + 1


def test_enemy_damage_grows_in_steps():
    every = CFG["damage_growth_every"]
    assert make_wave(every)["enemy_damage"] == (
        make_wave(0)["enemy_damage"] + CFG["damage_step"]
    )


def test_ranged_enemies_appear_only_after_start_wave():
    start = CFG["ranged_start_wave"]
    if start > 0:
        assert make_wave(start - 1)["ranged_every"] == 0
    assert make_wave(start)["ranged_every"] > 0


def test_ranged_every_has_lower_bound():
    # Доля дальнобойных растёт, но ranged_every не падает ниже минимума.
    assert make_wave(999)["ranged_every"] == CFG["ranged_every_min"]


def test_wave_has_all_keys():
    wave = make_wave(0)
    expected = {
        "count",
        "interval",
        "ranged_every",
        "enemy_hp",
        "enemy_speed",
        "enemy_damage",
    }
    assert set(wave) == expected
