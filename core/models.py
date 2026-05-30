import math


class Obstacle:
    def __init__(self, x, y, width, height, asset):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.asset = asset

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
