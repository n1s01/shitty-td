"""Игровой движок: обновление врагов, снарядов, монет и волн."""

import math
import random

from config import GAME_CONFIG
from core.grid import Grid
from core.map_generator import WATER, MapGenerator
from core.models import Coin, Enemy, Projectile, RangedEnemy, ShatterEffect, Tower
from core.pathfinding import find_path, smooth_path
from core.upgrades import effective_stats
from core.wave_generator import make_wave


class GameEngine:
    """Состояние и логика игры"""

    def __init__(self, width, height, stats=None):
        """Создаёт партию: башню, карту, сетку и счётчики.

        Args:
            width: ширина игрового поля в пикселях.
            height: высота игрового поля в пикселях.
            stats: словарь характеристик башни из улучшений; если None,
                берутся базовые статы без улучшений.
        """
        if stats is None:
            stats = effective_stats({"coins": 0, "upgrades": {}})
        self.width = width
        self.height = height
        self.fire_cooldown_max = stats["tower_fire_cooldown"]
        self.projectile_damage = stats["projectile_damage"]
        self.auto_fire = stats["auto_fire"]
        self.auto_wave = stats["auto_wave"]
        self.auto_collect = stats["auto_collect"]
        self.obstacle_breaks_left = stats["obstacle_breaks"]
        self.tower = Tower(
            x=width / 2,
            y=height / 2,
            size=GAME_CONFIG["tower_size"],
            max_hp=stats["tower_max_hp"],
            hitbox_size=GAME_CONFIG["tower_hitbox_size"],
        )
        self.enemies = []
        self.projectiles = []
        self.enemy_projectiles = []
        self.coins = []
        self.effects = []
        self.balance = 0
        self.kills = 0
        self.grid = Grid(
            width, height, GAME_CONFIG["grid_cols"], GAME_CONFIG["grid_rows"]
        )
        generated = MapGenerator(width, height, self.tower.x, self.tower.y).generate()
        self.biome_map = generated.biomes
        self.tile_cols = generated.cols
        self.tile_rows = generated.rows
        self.tile_size = generated.tile_size
        self.decor = generated.decor
        self.obstacles = generated.obstacles
        self._mark_map_on_grid()
        self.spawn_timer = 0
        self.spawned_this_wave = 0
        self.wave_index = 0
        self.wave_active = True
        self.tower_shoot_timer = 0
        self.tower_last_shot_dir = (1, 0)
        self.fire_cooldown = 0
        self.is_game_over = False

    def update(self):
        """Продвигает всё состояние партии на один кадр."""
        if self.is_game_over:
            return
        if self.tower_shoot_timer > 0:
            self.tower_shoot_timer -= 1
        if self.fire_cooldown > 0:
            self.fire_cooldown -= 1
        self._handle_spawning()
        self._update_enemies()
        self._update_projectiles()
        self._update_enemy_projectiles()
        self._update_coins()
        self._update_effects()

    def shoot_at(self, target_x, target_y):
        """Выпускает снаряд башни в сторону точки, если не идёт перезарядка.

        Args:
            target_x: координата цели по горизонтали.
            target_y: координата цели по вертикали.
        """
        if self.fire_cooldown > 0:
            return
        dx = target_x - self.tower.x
        dy = target_y - self.tower.y
        dist = math.hypot(dx, dy)
        if dist > 0:
            self.projectiles.append(
                Projectile(
                    x=self.tower.x,
                    y=self.tower.y,
                    vx=dx / dist,
                    vy=dy / dist,
                    speed=GAME_CONFIG["projectile_speed"],
                    damage=self.projectile_damage,
                )
            )
            self.tower_shoot_timer = GAME_CONFIG["tower_shoot_anim_frames"]
            self.tower_last_shot_dir = (dx / dist, dy / dist)
            self.fire_cooldown = self.fire_cooldown_max

    @property
    def reload_progress(self):
        """Готовность перезарядки от 0.0 (только выстрелил) до 1"""
        max_cd = self.fire_cooldown_max
        if max_cd <= 0 or self.fire_cooldown <= 0:
            return 1.0
        return 1.0 - self.fire_cooldown / max_cd

    @property
    def wave_progress(self):
        """Доля заспавненных врагов текущей волны от 0.0 до 1"""
        if not self.wave_active:
            return 1.0
        wave = make_wave(self.wave_index)
        return self.spawned_this_wave / max(1, wave["count"])

    @property
    def wave_ready(self):
        """True, если волна завершена и можно запускать следующую."""
        return not self.wave_active and not self.is_game_over

    def start_wave(self):
        """Запускает новую волну, сбрасывая счётчики спавна."""
        self.wave_active = True
        self.spawned_this_wave = 0
        self.spawn_timer = 0

    def _handle_spawning(self):
        """Спавнит врагов по таймеру и завершает волну."""
        if not self.wave_active:
            return
        wave = make_wave(self.wave_index)
        max_alive = GAME_CONFIG["endless"]["max_alive"]
        if self.spawned_this_wave < wave["count"]:
            self.spawn_timer += 1
            if self.spawn_timer >= wave["interval"] and len(self.enemies) < max_alive:
                self.spawn_timer = 0
                self._spawn_enemy(wave)
        elif not self.enemies:
            self.wave_active = False
            self.wave_index += 1

    def _spawn_enemy(self, wave):
        """Создаёт врага у случайного края и прокладывает ему путь.

        Каждый ranged_every-й враг волны делается стреляющим

        Args:
            wave: словарь параметров волны из make_wave.
        """
        side = random.randint(0, 3)
        size = GAME_CONFIG["enemy_size"]
        if side == 0:
            x, y = random.uniform(0, self.width), -size
        elif side == 1:
            x, y = self.width + size, random.uniform(0, self.height)
        elif side == 2:
            x, y = random.uniform(0, self.width), self.height + size
        else:
            x, y = -size, random.uniform(0, self.height)

        ranged_every = wave["ranged_every"]
        is_ranged = ranged_every > 0 and self.spawned_this_wave % ranged_every == 0
        if is_ranged:
            enemy = RangedEnemy(
                x=x,
                y=y,
                size=size,
                hp=wave["enemy_hp"],
                speed=wave["enemy_speed"],
                damage=wave["enemy_damage"],
                attack_range=GAME_CONFIG["ranged_enemy_range"],
                fire_rate=GAME_CONFIG["ranged_enemy_fire_rate"],
                initial_delay=GAME_CONFIG["ranged_enemy_initial_delay"],
            )
        else:
            enemy = Enemy(
                x=x,
                y=y,
                size=size,
                hp=wave["enemy_hp"],
                speed=wave["enemy_speed"],
                damage=wave["enemy_damage"],
            )

        self.spawned_this_wave += 1
        self._assign_path(enemy)
        self.enemies.append(enemy)

    def _mark_map_on_grid(self):
        """Отмечает воду и сплошные препятствия как непроходимые клетки."""
        ts = self.tile_size
        for row in range(self.tile_rows):
            for col in range(self.tile_cols):
                if self.biome_map[row][col] == WATER:
                    self._mark_world_rect(col * ts, row * ts, ts, ts)
        for obstacle in self.obstacles:
            if not obstacle.solid:
                continue
            x, y, width, height = obstacle.rect
            self._mark_world_rect(x, y, width, height)

    def _mark_world_rect(self, x, y, width, height):
        """Помечает все клетки сетки под прямоугольником как препятствия.

        Args:
            x: левая граница прямоугольника в пикселях.
            y: верхняя граница прямоугольника в пикселях.
            width: ширина прямоугольника.
            height: высота прямоугольника.
        """
        left, top = self.grid.world_to_grid(x, y)
        right, bottom = self.grid.world_to_grid(x + width, y + height)
        for row in range(top, bottom + 1):
            for col in range(left, right + 1):
                self.grid.set_obstacle(col, row)

    def _assign_path(self, enemy):
        """Прокладывает врагу путь до башни и записывает его.

        Args:
            enemy: враг, которому назначается путь.
        """
        start = self.grid.world_to_grid(enemy.x, enemy.y)
        end = self.grid.world_to_grid(self.tower.x, self.tower.y)
        grid_path = find_path(self.grid, start, end)
        if grid_path:
            grid_path = smooth_path(self.grid, grid_path)
            enemy.path = [self.grid.grid_to_world(c, r) for c, r in grid_path]
            enemy.path_index = 0

    def remove_obstacle(self, obstacle):
        """Удаляет препятствие и при необходимости пересчитывает пути.

        Args:
            obstacle: препятствие для удаления.

        Returns:
            True, если препятствие было удалено, иначе False.
        """
        if obstacle not in self.obstacles:
            return False
        self.obstacles.remove(obstacle)
        if obstacle.solid:
            self.grid = Grid(
                self.width,
                self.height,
                GAME_CONFIG["grid_cols"],
                GAME_CONFIG["grid_rows"],
            )
            self._mark_map_on_grid()
            for enemy in self.enemies:
                self._assign_path(enemy)
        return True

    def _update_enemies(self):
        """Двигает каждого врага к башне и выполняет его действие."""
        for enemy in self.enemies[:]:
            enemy.move_towards(self.tower.x, self.tower.y)
            enemy.act(self)

    def damage_tower(self, amount):
        """Наносит урон башне и фиксирует проигрыш при её разрушении.

        Args:
            amount: величина урона.
        """
        self.tower.take_damage(amount)
        if self.tower.is_destroyed:
            self.is_game_over = True

    def tower_contact(self, enemy):
        """Проверяет, касается ли враг зоны попаданий башни.

        Args:
            enemy: проверяемый враг.

        Returns:
            True, если враг соприкасается с башней, иначе False.
        """
        return _circle_touches_rect(
            enemy.x, enemy.y, enemy.size / 2, self.tower.hitbox_rect
        )

    def fire_enemy_projectile(self, enemy):
        """Создаёт снаряд врага, летящий в башню.

        Args:
            enemy: дальнобойный враг, совершающий выстрел.
        """
        dx = self.tower.x - enemy.x
        dy = self.tower.y - enemy.y
        dist = math.hypot(dx, dy)
        if dist > 0:
            self.enemy_projectiles.append(
                Projectile(
                    x=enemy.x,
                    y=enemy.y,
                    vx=dx / dist,
                    vy=dy / dist,
                    speed=GAME_CONFIG["ranged_enemy_projectile_speed"],
                    damage=enemy.damage,
                )
            )

    def _update_enemy_projectiles(self):
        """Двигает снаряды врагов, бьёт башню и убирает лишние."""
        for proj in self.enemy_projectiles[:]:
            proj.update()
            if _point_in_rect(proj.x, proj.y, self.tower.hitbox_rect):
                self.damage_tower(proj.damage)
                self.enemy_projectiles.remove(proj)
            elif self._is_out_of_bounds(proj):
                self.enemy_projectiles.remove(proj)

    def _update_projectiles(self):
        """Двигает снаряды башни и обрабатывает их попадания."""
        proj_size = GAME_CONFIG["projectile_size"]
        for proj in self.projectiles[:]:
            proj.update()
            if self._check_projectile_hits(proj, proj_size):
                continue
            if self._hits_obstacle(proj):
                self.effects.append(
                    ShatterEffect(proj.x, proj.y, GAME_CONFIG["shatter_color"])
                )
                self.projectiles.remove(proj)
                continue
            if self._is_out_of_bounds(proj):
                self.projectiles.remove(proj)

    def _hits_obstacle(self, proj):
        """Проверяет, попал ли снаряд в сплошное препятствие.

        Args:
            proj: снаряд башни.

        Returns:
            True, если снаряд внутри сплошного препятствия, иначе False.
        """
        for obstacle in self.obstacles:
            if not obstacle.solid:
                continue
            ox, oy, ow, oh = obstacle.rect
            inset = 4
            if ox + inset <= proj.x <= ox + ow - inset:
                if oy + inset <= proj.y <= oy + oh - inset:
                    return True
        return False

    def _update_effects(self):
        """Обновляет визуальные эффекты и убирает завершённые."""
        for effect in self.effects[:]:
            effect.update()
            if effect.is_done:
                self.effects.remove(effect)

    def _check_projectile_hits(self, proj, proj_size):
        """Проверяет попадание снаряда по врагам и применяет урон.

        При смерти врага начисляет убийство и роняет монеты.

        Args:
            proj: снаряд башни.
            proj_size: радиус снаряда для проверки столкновения.

        Returns:
            True, если снаряд попал во врага (и был удалён), иначе False.
        """
        for enemy in self.enemies[:]:
            dist = math.hypot(proj.x - enemy.x, proj.y - enemy.y)
            if dist < (enemy.size + proj_size):
                enemy.take_damage(proj.damage)
                enemy.knockback_vx = proj.vx * GAME_CONFIG["knockback_force"]
                enemy.knockback_vy = proj.vy * GAME_CONFIG["knockback_force"]
                enemy.hit_flash_time = GAME_CONFIG["hit_flash_frames"]
                enemy.on_hit()
                if enemy.is_dead:
                    self.enemies.remove(enemy)
                    self.kills += 1
                    for i in range(enemy.coin_value):
                        angle = random.uniform(0, 2 * math.pi)
                        speed = random.uniform(2.0, 4.5)
                        self.coins.append(
                            Coin(
                                enemy.x,
                                enemy.y,
                                1,
                                vx=math.cos(angle) * speed,
                                vy=math.sin(angle) * speed,
                                anim_phase=random.randint(0, 62),
                            )
                        )
                self.projectiles.remove(proj)
                return True
        return False

    def _update_coins(self):
        """Обновляет монеты и зачисляет собранные в баланс."""
        alive = []
        for coin in self.coins:
            coin.update()
            if coin.pending_collect:
                self.balance += coin.value
            else:
                alive.append(coin)
        self.coins = alive

    def collect_coin_at(self, x, y, target_x, target_y):
        """Начинает сбор монет рядом с указанной точкой.

        Args:
            x: координата точки сбора по горизонтали.
            y: координата точки сбора по вертикали.
            target_x: координата, к которой летит монета (по горизонтали).
            target_y: координата, к которой летит монета (по вертикали).
        """
        from config import COIN_CONFIG

        radius = COIN_CONFIG["collect_hitbox"]
        for coin in self.coins:
            if not coin.collecting and math.hypot(x - coin.x, y - coin.y) <= radius:
                self._begin_collect(coin, target_x, target_y)

    def auto_collect_coins(self, target_x, target_y):
        """Автоматически запускает сбор всех монет на поле.

        Args:
            target_x: координата цели сбора по горизонтали.
            target_y: координата цели сбора по вертикали.
        """
        for coin in self.coins:
            if not coin.collecting:
                self._begin_collect(coin, target_x, target_y)

    def _begin_collect(self, coin, target_x, target_y):
        """Запускает полёт монеты к цели по случайной дуге.

        Args:
            coin: монета, которую нужно собрать.
            target_x: координата цели по горизонтали.
            target_y: координата цели по вертикали.
        """
        mx = (coin.x + target_x) / 2
        my = (coin.y + target_y) / 2
        dx = target_x - coin.x
        dy = target_y - coin.y
        length = max(1.0, math.hypot(dx, dy))
        sign = random.choice((-1, 1))
        offset = random.uniform(80, 160)
        cx = mx + (-dy / length) * sign * offset
        cy = my + (dx / length) * sign * offset
        coin.start_collect(target_x, target_y, cx, cy)

    def _is_out_of_bounds(self, proj):
        """Проверяет, вышел ли снаряд за пределы поля.

        Args:
            proj: проверяемый снаряд.

        Returns:
            True, если снаряд за границами поля, иначе False.
        """
        return proj.x < 0 or proj.x > self.width or proj.y < 0 or proj.y > self.height


def _circle_touches_rect(cx, cy, radius, rect):
    """Проверяет пересечение окружности и прямоугольника.

    Args:
        cx: центр окружности по горизонтали.
        cy: центр окружности по вертикали.
        radius: радиус окружности.
        rect: прямоугольник как (x, y, width, height).

    Returns:
        True, если окружность касается прямоугольника, иначе False.
    """
    rx, ry, rw, rh = rect
    nearest_x = max(rx, min(cx, rx + rw))
    nearest_y = max(ry, min(cy, ry + rh))
    return math.hypot(cx - nearest_x, cy - nearest_y) <= radius


def _point_in_rect(x, y, rect):
    """Проверяет, лежит ли точка внутри прямоугольника.

    Args:
        x: координата точки по горизонтали.
        y: координата точки по вертикали.
        rect: прямоугольник как (x, y, width, height).

    Returns:
        True, если точка внутри прямоугольника, иначе False.
    """
    rx, ry, rw, rh = rect
    return rx <= x <= rx + rw and ry <= y <= ry + rh
