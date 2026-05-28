import math
import random
from config import GAME_CONFIG
from core.models import Tower, Enemy, Projectile


class GameEngine:
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.tower = Tower(
            x=width / 2,
            y=height / 2,
            size=GAME_CONFIG["tower_size"],
            max_hp=GAME_CONFIG["tower_max_hp"],
        )
        self.enemies = []
        self.projectiles = []
        self.spawn_timer = 0
        self.is_game_over = False

    def update(self):
        if self.is_game_over:
            return
        self._handle_spawning()
        self._update_enemies()
        self._update_projectiles()

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

    def _handle_spawning(self):
        self.spawn_timer += 1
        if self.spawn_timer >= GAME_CONFIG["enemy_spawn_delay"]:
            self.spawn_timer = 0
            self._spawn_enemy()

    def _spawn_enemy(self):
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

        self.enemies.append(
            Enemy(
                x=x, y=y, size=size,
                hp=GAME_CONFIG["enemy_max_hp"],
                speed=GAME_CONFIG["enemy_speed"],
                damage=GAME_CONFIG["enemy_damage"],
            )
        )

    def _update_enemies(self):
        for enemy in self.enemies[:]:
            enemy.move_towards(self.tower.x, self.tower.y)
            dist = math.hypot(enemy.x - self.tower.x, enemy.y - self.tower.y)
            if dist <= (self.tower.size / 2 + enemy.size / 2):
                self.tower.take_damage(enemy.damage)
                self.enemies.remove(enemy)
                if self.tower.is_destroyed:
                    self.is_game_over = True

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
