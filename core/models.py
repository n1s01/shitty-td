import math


class Tower:
    def __init__(self, x, y, size, max_hp):
        self.x = x
        self.y = y
        self.size = size
        self.hp = max_hp
        self.max_hp = max_hp

    def take_damage(self, amount):
        self.hp = max(0, self.hp - amount)

    @property
    def is_destroyed(self):
        return self.hp <= 0


class Enemy:
    def __init__(self, x, y, size, hp, speed, damage):
        self.x = x
        self.y = y
        self.size = size
        self.hp = hp
        self.max_hp = hp
        self.speed = speed
        self.damage = damage

    def move_towards(self, target_x, target_y):
        dx = target_x - self.x
        dy = target_y - self.y
        dist = math.hypot(dx, dy)
        if dist > 0:
            self.x += (dx / dist) * self.speed
            self.y += (dy / dist) * self.speed

    def take_damage(self, amount):
        self.hp -= amount

    @property
    def is_dead(self):
        return self.hp <= 0


class RangedEnemy(Enemy):
    def __init__(self, x, y, size, hp, speed, damage, attack_range, fire_rate) -> None:
        super().__init__(x, y, size, hp, speed, damage)
        self.attack_range = attack_range
        self.fire_rate = fire_rate
        self.fire_cooldown = 0

    def move_towards(self, target_x, target_y):
        dx = target_x - self.x
        dy = target_y - self.y
        dist = math.hypot(dx, dy)
        if dist > self.attack_range:
            self.x += (dx / dist) * self.speed
            self.y += (dy / dist) * self.speed

    def can_fire(self):
        return self.fire_cooldown == 0

    def reset_cooldown(self):
        self.fire_cooldown = self.fire_rate

    def update_cooldown(self):
        if self.fire_cooldown > 0:
            self.fire_cooldown -= 1

    def in_range(self, target_x, target_y):
        dx = target_x - self.x
        dy = target_y - self.y
        return math.hypot(dx, dy) <= self.attack_range


class Projectile:
    def __init__(self, x, y, vx, vy, speed):
        self.x = x
        self.y = y
        self.vx = vx
        self.vy = vy
        self.speed = speed

    def update(self):
        self.x += self.vx * self.speed
        self.y += self.vy * self.speed


class EnemyProjectile:
    def __init__(self, x, y, vx, vy, speed, damage) -> None:
        self.x = x
        self.y = y
        self.vx = vx
        self.vy = vy
        self.speed = speed
        self.damage = damage

    def update(self):
        self.x += self.vx * self.speed
        self.y += self.vy * self.speed
