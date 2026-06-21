"""Тесты для игровых объектов (core/models.py).

Башня, враги, монеты, снаряды. Проверяем урон, движение, дальнобойных
врагов и физику снарядов/монет.
"""

import pytest

from core.models import (
    Coin,
    Enemy,
    Obstacle,
    Projectile,
    RangedEnemy,
    Tower,
)


def test_tower_starts_full_hp():
    tower = Tower(x=0, y=0, size=50, max_hp=100)
    assert tower.hp == 100
    assert not tower.is_destroyed


def test_tower_take_damage():
    tower = Tower(0, 0, 50, 100)
    tower.take_damage(30)
    assert tower.hp == 70


def test_tower_hp_never_negative():
    tower = Tower(0, 0, 50, 100)
    tower.take_damage(150)
    assert tower.hp == 0
    assert tower.is_destroyed


def test_tower_hitbox_defaults_to_size():
    tower = Tower(0, 0, 50, 100)
    assert tower.hitbox_size == 50


def test_tower_hitbox_rect_centered():
    tower = Tower(100, 100, 50, 100, hitbox_size=20)
    x, y, w, h = tower.hitbox_rect
    assert (w, h) == (20, 20)
    assert (x, y) == (90, 90)  # центр 100,100 минус половина 10


def test_enemy_take_damage_and_death():
    enemy = Enemy(0, 0, size=20, hp=3, speed=1, damage=1)
    enemy.take_damage(1)
    assert not enemy.is_dead
    enemy.take_damage(5)
    assert enemy.is_dead


def test_enemy_distance_to():
    enemy = Enemy(0, 0, 20, 3, 1, 1)
    assert enemy.distance_to(3, 4) == pytest.approx(5.0)


def test_enemy_moves_towards_target():
    enemy = Enemy(0, 0, 20, 3, speed=2, damage=1)
    enemy.move_towards(100, 0)
    # Двигается вдоль X на величину скорости.
    assert enemy.x == pytest.approx(2)
    assert enemy.y == pytest.approx(0)


def test_enemy_snaps_to_close_target():
    enemy = Enemy(0, 0, 20, 3, speed=5, damage=1)
    # Цель ближе, чем шаг скорости - встаёт точно в неё.
    enemy.move_towards(1, 0)
    assert enemy.x == pytest.approx(1)


def test_enemy_follows_path_then_advances_index():
    enemy = Enemy(0, 0, 20, 3, speed=5, damage=1)
    enemy.path = [(2, 0), (10, 0)]
    enemy.move_towards(999, 999)  # fallback игнорируется, идёт по path
    assert enemy.path_index == 1
    assert (enemy.x, enemy.y) == pytest.approx((2, 0))


def test_knockback_decays_to_zero():
    enemy = Enemy(50, 50, 20, 3, speed=0, damage=1)
    enemy.knockback_vx = 4
    enemy.knockback_vy = 0
    # Гоняем тики, пока отдача не затухнет.
    for _ in range(50):
        enemy.tick_status()
    assert enemy.knockback_vx == 0
    assert enemy.knockback_vy == 0


def test_hit_flash_counts_down():
    enemy = Enemy(0, 0, 20, 3, 1, 1)
    enemy.hit_flash_time = 3
    enemy.tick_status()
    assert enemy.hit_flash_time == 2


def test_ranged_enemy_stops_in_range():
    enemy = RangedEnemy(
        0,
        0,
        20,
        3,
        speed=5,
        damage=1,
        attack_range=100,
        fire_rate=90,
        initial_delay=10,
    )
    enemy.move_towards(50, 0)  # в пределах дальности
    # Не двигается, стоит и стреляет.
    assert (enemy.x, enemy.y) == (0, 0)


def test_ranged_enemy_approaches_when_far():
    enemy = RangedEnemy(
        0,
        0,
        20,
        3,
        speed=2,
        damage=1,
        attack_range=10,
        fire_rate=90,
        initial_delay=10,
    )
    enemy.move_towards(100, 0)  # далеко -> приближается
    assert enemy.x == pytest.approx(2)


def test_ranged_enemy_fire_cooldown_cycle():
    enemy = RangedEnemy(
        0,
        0,
        20,
        3,
        1,
        1,
        attack_range=100,
        fire_rate=5,
        initial_delay=2,
    )
    assert not enemy.can_fire()
    enemy.update_cooldown()
    enemy.update_cooldown()
    assert enemy.can_fire()
    enemy.reset_cooldown()
    assert enemy.fire_cooldown == 5
    assert not enemy.can_fire()


def test_ranged_enemy_in_range_check():
    enemy = RangedEnemy(
        0,
        0,
        20,
        3,
        1,
        1,
        attack_range=10,
        fire_rate=5,
        initial_delay=0,
    )
    assert enemy.in_range(5, 0)
    assert not enemy.in_range(50, 0)


def test_ranged_enemy_gives_more_coins():
    assert RangedEnemy.coin_value > Enemy.coin_value


def test_projectile_moves_by_velocity_times_speed():
    p = Projectile(0, 0, vx=1, vy=0, speed=8, damage=1)
    p.update()
    assert p.x == 8
    assert p.y == 0


def test_projectile_diagonal():
    p = Projectile(0, 0, vx=0, vy=-1, speed=4, damage=1)
    p.update()
    assert p.y == -4


def test_coin_drops_then_idles():
    coin = Coin(0, 0, value=1, vx=10, vy=0)
    assert coin.is_dropping
    start_x = coin.x
    coin.update()
    assert coin.x > start_x  # пока летит по инерции
    # Долетаем до конца фазы падения.
    while coin.is_dropping:
        coin.update()
    assert not coin.is_dropping


def test_coin_collect_animation_finishes():
    coin = Coin(0, 0, value=1)
    coin.start_collect(tx=100, ty=100, cx=50, cy=0)
    assert coin.collecting
    # Прогоняем анимацию сбора до конца.
    for _ in range(500):
        coin.update()
        if coin.pending_collect:
            break
    assert coin.pending_collect
    assert coin.x == pytest.approx(100)
    assert coin.y == pytest.approx(100)


def test_obstacle_rect_centered():
    obs = Obstacle(x=100, y=100, width=40, height=20, asset="x")
    left, top, w, h = obs.rect
    assert (left, top) == (80, 90)
    assert (w, h) == (40, 20)


def test_obstacle_solid_default():
    assert Obstacle(0, 0, 10, 10, "x").solid is True
    assert Obstacle(0, 0, 10, 10, "x", solid=False).solid is False
