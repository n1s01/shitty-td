import math
import random

from config import GAME_CONFIG
from core.grid import Grid
from core.models import Enemy, Obstacle, Projectile, RangedEnemy, Tower
from core.pathfinding import find_path, smooth_path


class GameEngine:
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.tower = Tower(
            x=width / 2,
            y=height / 2,
            size=GAME_CONFIG["tower_size"],
            max_hp=GAME_CONFIG["tower_max_hp"],
            hitbox_size=GAME_CONFIG["tower_hitbox_size"],
        )
        self.enemies = []
        self.projectiles = []
        self.enemy_projectiles = []
        self.obstacles = []
        self.grid = Grid(
            width, height, GAME_CONFIG["grid_cols"], GAME_CONFIG["grid_rows"]
        )
        self._generate_obstacles()
        self.spawn_timer = 0
        self.spawned_this_wave = 0
        self.wave_index = 0
        self.wave_active = True
        self.tower_shoot_timer = 0
        self.tower_last_shot_dir = (1, 0)
        self.is_game_over = False

    def update(self):
        if self.is_game_over:
            return
        if self.tower_shoot_timer > 0:
            self.tower_shoot_timer -= 1
        self._handle_spawning()
        self._update_enemies()
        self._update_projectiles()
        self._update_enemy_projectiles()

    def shoot_at(self, target_x, target_y):
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
                )
            )
            self.tower_shoot_timer = GAME_CONFIG["tower_shoot_anim_frames"]
            self.tower_last_shot_dir = (dx / dist, dy / dist)

    @property
    def wave_progress(self):
        if not self.wave_active or self.wave_index >= len(GAME_CONFIG["waves"]):
            return 1.0
        wave = GAME_CONFIG["waves"][self.wave_index]
        return self.spawned_this_wave / max(1, wave["count"])

    @property
    def wave_ready(self):
        waves = GAME_CONFIG["waves"]
        return (
            not self.wave_active
            and not self.is_game_over
            and self.wave_index < len(waves)
        )

    @property
    def is_victory(self):
        return (
            not self.wave_active
            and self.wave_index >= len(GAME_CONFIG["waves"])
            and not self.enemies
        )

    def start_wave(self):
        self.wave_active = True
        self.spawned_this_wave = 0
        self.spawn_timer = 0

    def _handle_spawning(self):
        if not self.wave_active:
            return
        wave = GAME_CONFIG["waves"][self.wave_index]
        if self.spawned_this_wave < wave["count"]:
            self.spawn_timer += 1
            if self.spawn_timer >= wave["interval"]:
                self.spawn_timer = 0
                self._spawn_enemy(wave)
        elif not self.enemies:
            self.wave_active = False
            self.wave_index += 1

    def _spawn_enemy(self, wave):
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
                hp=GAME_CONFIG["enemy_max_hp"],
                speed=GAME_CONFIG["enemy_speed"],
                damage=GAME_CONFIG["enemy_damage"],
                attack_range=GAME_CONFIG["ranged_enemy_range"],
                fire_rate=GAME_CONFIG["ranged_enemy_fire_rate"],
                initial_delay=GAME_CONFIG["ranged_enemy_initial_delay"],
            )
        else:
            enemy = Enemy(
                x=x,
                y=y,
                size=size,
                hp=GAME_CONFIG["enemy_max_hp"],
                speed=GAME_CONFIG["enemy_speed"],
                damage=GAME_CONFIG["enemy_damage"],
            )

        self.spawned_this_wave += 1
        self._assign_path(enemy)
        self.enemies.append(enemy)

    def _generate_obstacles(self):
        specs = GAME_CONFIG["map_obstacles"]
        target_count = GAME_CONFIG["map_obstacle_count"]
        attempts = 0
        safe_radius = (
            max(self.width, self.height)
            * GAME_CONFIG["map_obstacle_safe_radius_factor"]
        )

        while len(self.obstacles) < target_count and attempts < target_count * 20:
            attempts += 1
            spec = random.choice(specs)
            width, height = spec["size"]
            x = random.uniform(width, self.width - width)
            y = random.uniform(height, self.height - height)

            if math.hypot(x - self.tower.x, y - self.tower.y) < safe_radius:
                continue

            obstacle = Obstacle(
                x=x, y=y, width=width, height=height, asset=spec["asset"]
            )
            if self._overlaps_existing_obstacle(obstacle):
                continue

            self.obstacles.append(obstacle)
            self._mark_obstacle_on_grid(obstacle)

    def _overlaps_existing_obstacle(self, obstacle):
        ox, oy, ow, oh = obstacle.rect
        padded = (ox - 18, oy - 18, ow + 36, oh + 36)
        for other in self.obstacles:
            rx, ry, rw, rh = other.rect
            if _rects_overlap(padded, (rx, ry, rw, rh)):
                return True
        return False

    def _mark_obstacle_on_grid(self, obstacle):
        x, y, width, height = obstacle.rect
        left, top = self.grid.world_to_grid(x, y)
        right, bottom = self.grid.world_to_grid(x + width, y + height)
        for row in range(top, bottom + 1):
            for col in range(left, right + 1):
                self.grid.set_obstacle(col, row)

    def _assign_path(self, enemy):
        start = self.grid.world_to_grid(enemy.x, enemy.y)
        end = self.grid.world_to_grid(self.tower.x, self.tower.y)
        grid_path = find_path(self.grid, start, end)
        if grid_path:
            grid_path = smooth_path(self.grid, grid_path)
            enemy.path = [self.grid.grid_to_world(c, r) for c, r in grid_path]

    def _update_enemies(self):
        for enemy in self.enemies[:]:  # copy list with enemies in mem
            enemy.move_towards(self.tower.x, self.tower.y)

            if isinstance(enemy, RangedEnemy):
                if enemy.in_range(self.tower.x, self.tower.y):
                    enemy.update_cooldown()
                    if enemy.can_fire():
                        self._enemy_shoot(enemy)
                        enemy.reset_cooldown()
            else:
                if _circle_touches_rect(
                    enemy.x, enemy.y, enemy.size / 2, self.tower.hitbox_rect
                ):
                    self.tower.take_damage(enemy.damage)
                    self.enemies.remove(enemy)
                    if self.tower.is_destroyed:
                        self.is_game_over = True

    def _enemy_shoot(self, enemy):
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
                    damage=GAME_CONFIG["enemy_damage"],
                )
            )

    def _update_enemy_projectiles(self):
        for proj in self.enemy_projectiles[:]:
            proj.update()
            if _point_in_rect(proj.x, proj.y, self.tower.hitbox_rect):
                self.tower.take_damage(proj.damage)
                self.enemy_projectiles.remove(proj)
                if self.tower.is_destroyed:
                    self.is_game_over = True
            elif self._is_out_of_bounds(proj):
                self.enemy_projectiles.remove(proj)

    def _update_projectiles(self):
        proj_size = GAME_CONFIG["projectile_size"]
        for proj in self.projectiles[:]:
            proj.update()
            if self._check_projectile_hits(proj, proj_size):
                continue
            if self._is_out_of_bounds(proj):
                self.projectiles.remove(proj)

    def _check_projectile_hits(self, proj, proj_size):
        for enemy in self.enemies[:]:
            dist = math.hypot(proj.x - enemy.x, proj.y - enemy.y)
            if dist < (enemy.size + proj_size):
                enemy.take_damage(1)
                if enemy.is_dead:
                    self.enemies.remove(enemy)
                self.projectiles.remove(proj)
                return True
        return False

    def _is_out_of_bounds(self, proj):
        return proj.x < 0 or proj.x > self.width or proj.y < 0 or proj.y > self.height


def _rects_overlap(a, b):
    ax, ay, aw, ah = a
    bx, by, bw, bh = b
    return ax < bx + bw and ax + aw > bx and ay < by + bh and ay + ah > by


def _circle_touches_rect(cx, cy, radius, rect):
    rx, ry, rw, rh = rect
    nearest_x = max(rx, min(cx, rx + rw))
    nearest_y = max(ry, min(cy, ry + rh))
    return math.hypot(cx - nearest_x, cy - nearest_y) <= radius


def _point_in_rect(x, y, rect):
    rx, ry, rw, rh = rect
    return rx <= x <= rx + rw and ry <= y <= ry + rh
