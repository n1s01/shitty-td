"""Тесты для системы улучшений (core/upgrades.py).

Профиль игрока - словарь {"coins": ..., "upgrades": {uid: level}}.
Тут проверяем покупку улучшений, разблокировку главного и пересчёт статов.
"""

import pytest

from config import GAME_CONFIG, UPGRADES
from core import upgrades


def fresh_profile(coins=0):
    return {"coins": coins, "upgrades": {}}


def max_out_side_upgrades(profile):
    """Прокачивает все боковые улучшения до максимума."""
    for uid, spec in UPGRADES.items():
        if spec["kind"] == "side":
            profile["upgrades"][uid] = spec["max_level"]


def test_level_of_unbought_is_zero():
    assert upgrades.level(fresh_profile(), "auto_fire") == 0


def test_side_upgrade_is_always_unlocked():
    assert upgrades.is_unlocked(fresh_profile(), "auto_fire")


def test_main_upgrade_locked_until_sides_maxed():
    profile = fresh_profile()
    assert not upgrades.is_unlocked(profile, "tavern")
    max_out_side_upgrades(profile)
    assert upgrades.is_unlocked(profile, "tavern")


def test_can_buy_requires_enough_coins():
    cost = UPGRADES["auto_wave"]["cost"]
    assert not upgrades.can_buy(fresh_profile(coins=cost - 1), "auto_wave")
    assert upgrades.can_buy(fresh_profile(coins=cost), "auto_wave")


def test_buy_deducts_coins_and_raises_level():
    cost = UPGRADES["auto_wave"]["cost"]
    profile = fresh_profile(coins=cost + 10)
    assert upgrades.buy(profile, "auto_wave") is True
    assert profile["coins"] == 10
    assert upgrades.level(profile, "auto_wave") == 1


def test_buy_fails_without_coins():
    profile = fresh_profile(coins=0)
    assert upgrades.buy(profile, "auto_wave") is False
    assert profile["coins"] == 0
    assert upgrades.level(profile, "auto_wave") == 0


def test_cannot_buy_maxed_upgrade():
    profile = fresh_profile(coins=10_000)
    upgrades.buy(profile, "auto_wave")  # max_level == 1
    assert upgrades.is_maxed(profile, "auto_wave")
    assert not upgrades.can_buy(profile, "auto_wave")
    assert upgrades.buy(profile, "auto_wave") is False


def test_cannot_buy_main_while_locked_even_with_coins():
    profile = fresh_profile(coins=10_000)
    assert not upgrades.can_buy(profile, "tavern")
    assert upgrades.buy(profile, "tavern") is False


def test_effective_stats_default_equal_base():
    stats = upgrades.effective_stats(fresh_profile())
    assert stats["tower_max_hp"] == GAME_CONFIG["tower_max_hp"]
    assert stats["tower_fire_cooldown"] == GAME_CONFIG["tower_fire_cooldown"]
    assert stats["projectile_damage"] == GAME_CONFIG["projectile_damage"]
    assert stats["auto_fire"] is False
    assert stats["auto_wave"] is False
    assert stats["auto_collect"] is False
    assert stats["obstacle_breaks"] == 0


def test_tavern_boosts_stats():
    profile = fresh_profile()
    profile["upgrades"]["tavern"] = 1
    stats = upgrades.effective_stats(profile)
    effects = UPGRADES["tavern"]["effects"]
    # Урон удваивается (+100%), HP растёт, кулдаун падает.
    assert stats["projectile_damage"] == pytest.approx(
        GAME_CONFIG["projectile_damage"] * (1 + effects["damage_mult"])
    )
    assert stats["tower_max_hp"] > GAME_CONFIG["tower_max_hp"]
    assert stats["tower_fire_cooldown"] < GAME_CONFIG["tower_fire_cooldown"]


def test_cooldown_never_below_one():
    # Даже при сильном уменьшении кулдаун остаётся >= 1.
    profile = fresh_profile()
    profile["upgrades"]["tavern"] = 100
    assert upgrades.effective_stats(profile)["tower_fire_cooldown"] >= 1


def test_flag_upgrades_reflected_in_stats():
    profile = fresh_profile()
    profile["upgrades"]["auto_fire"] = 1
    profile["upgrades"]["auto_collect"] = 1
    stats = upgrades.effective_stats(profile)
    assert stats["auto_fire"] is True
    assert stats["auto_collect"] is True
    assert stats["auto_wave"] is False
