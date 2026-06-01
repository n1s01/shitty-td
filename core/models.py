import math
import random

from config import COIN_CONFIG, GAME_CONFIG


class ShatterEffect:
    DURATION = 22

    def __init__(self, x, y, color, count=9):
        self.color = color
        self.timer = 0

        self.particles = []
        for _ in range(count):
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(1.2, 3.6)
            self.particles.append(
                [x, y, math.cos(angle) * speed, math.sin(angle) * speed]
            )

    def update(self):
        self.timer += 1
        for p in self.particles:
            p[0] += p[2]
            p[1] += p[3]
            p[2] *= 0.86
            p[3] *= 0.86

    @property
    def progress(self):
        return min(1.0, self.timer / self.DURATION)

    @property
    def is_done(self):
        return self.timer >= self.DURATION


class Obstacle:
    def __init__(self, x, y, width, height, asset, solid=True):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.asset = asset
        self.solid = solid

    @property
    def rect(self):
        return (
            self.x - self.width / 2,
            self.y - self.height / 2,
            self.width,
            self.height,
        )


class Tower:
    def __init__(self, x, y, size, max_hp, hitbox_size=None):
        self.x = x
        self.y = y
        self.size = size
        self.hitbox_size = hitbox_size or size
        self.hp = max_hp
        self.max_hp = max_hp

    def take_damage(self, amount):
        self.hp = max(0, self.hp - amount)

    @property
    def is_destroyed(self):
        return self.hp <= 0

    @property
    def hitbox_rect(self):
        half = self.hitbox_size / 2
        return (self.x - half, self.y - half, self.hitbox_size, self.hitbox_size)


class Enemy:
    coin_value = 1

    def __init__(self, x, y, size, hp, speed, damage):
        self.x = x
        self.y = y
        self.size = size
        self.hp = hp
        self.max_hp = hp
        self.speed = speed
        self.damage = damage
        self.path = None
        self.path_index = 0
        self.knockback_vx = 0
        self.knockback_vy = 0
        self.hit_flash_time = 0

    def move_towards(self, target_x, target_y):
        next_x, next_y = self._next_target(target_x, target_y)
        dx = next_x - self.x
        dy = next_y - self.y
        dist = math.hypot(dx, dy)
        if dist == 0:
            return
        if dist < self.speed:
            self.x = next_x
            self.y = next_y
            if self.path and self.path_index < len(self.path):
                self.path_index += 1
        else:
            self.x += (dx / dist) * self.speed
            self.y += (dy / dist) * self.speed
        if self.hit_flash_time > 0:
            self.hit_flash_time -= 1
        if self.knockback_vx != 0 or self.knockback_vy != 0:
            self.x += self.knockback_vx
            self.y += self.knockback_vy
            decay = GAME_CONFIG["knockback_decay"]
            self.knockback_vx *= decay
            self.knockback_vy *= decay
            if abs(self.knockback_vx) < 0.05 and abs(self.knockback_vy) < 0.05:
                self.knockback_vx = 0
                self.knockback_vy = 0

    def _next_target(self, fallback_x, fallback_y):
        if self.path and self.path_index < len(self.path):
            return self.path[self.path_index]
        return fallback_x, fallback_y

    def distance_to(self, x, y):
        return math.hypot(x - self.x, y - self.y)

    def take_damage(self, amount):
        self.hp -= amount

    @property
    def is_dead(self):
        return self.hp <= 0


class RangedEnemy(Enemy):
    coin_value = 2

    def __init__(
        self, x, y, size, hp, speed, damage, attack_range, fire_rate, initial_delay
    ):
        super().__init__(x, y, size, hp, speed, damage)
        self.attack_range = attack_range
        self.fire_rate = fire_rate
        self.fire_cooldown = initial_delay

    def move_towards(self, target_x, target_y):
        if self.distance_to(target_x, target_y) <= self.attack_range:
            return
        super().move_towards(target_x, target_y)

    def can_fire(self):
        return self.fire_cooldown <= 0

    def reset_cooldown(self):
        self.fire_cooldown = self.fire_rate

    def update_cooldown(self):
        if self.fire_cooldown > 0:
            self.fire_cooldown -= 1

    def in_range(self, target_x, target_y):
        return self.distance_to(target_x, target_y) <= self.attack_range


class Coin:
    _COLLECT_SPEED = 16

    def __init__(self, x, y, value, vx=0, vy=0, anim_phase=0):
        self.x = x
        self.y = y
        self.value = value
        self.vx = vx
        self.vy = vy
        self.drop_timer = COIN_CONFIG["drop_frames"]
        self.anim_tick = anim_phase
        self.collecting = False
        self.collect_tx = 0
        self.collect_ty = 0
        self.scale = 1.0
        self.pending_collect = False

    def start_collect(self, tx, ty, cx, cy):
        self.collecting = True
        self.collect_tx = tx
        self.collect_ty = ty
        self._sx = self.x
        self._sy = self.y
        self._cx = cx
        self._cy = cy
        self.collect_t = 0.0
        self.drop_timer = 0
        self.vx = 0
        self.vy = 0

    def update(self):
        if self.collecting:
            self.collect_t += 0.008 + self.collect_t * 0.055
            t = min(1.0, self.collect_t)
            mt = 1.0 - t
            self.x = (
                mt * mt * self._sx + 2 * mt * t * self._cx + t * t * self.collect_tx
            )
            self.y = (
                mt * mt * self._sy + 2 * mt * t * self._cy + t * t * self.collect_ty
            )
            self.scale = max(0.15, 1.0 - t * 0.85)
            if t >= 1.0:
                self.pending_collect = True
            return

        if self.drop_timer > 0:
            self.drop_timer -= 1
            self.x += self.vx
            self.y += self.vy
            f = COIN_CONFIG["drop_friction"]
            self.vx *= f
            self.vy *= f
        else:
            self.anim_tick += 1

    @property
    def is_dropping(self):
        return self.drop_timer > 0


class Projectile:
    def __init__(self, x, y, vx, vy, speed, damage=0):
        self.x = x
        self.y = y
        self.vx = vx
        self.vy = vy
        self.speed = speed
        self.damage = damage

    def update(self):
        self.x += self.vx * self.speed
        self.y += self.vy * self.speed
