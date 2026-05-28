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
