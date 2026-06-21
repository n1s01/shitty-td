"""Игровые объекты: башня, враги, монеты, снаряды и эффекты."""

import math
import random

from config import COIN_CONFIG, GAME_CONFIG


class ShatterEffect:
    """Эффект разлёта частиц при разрушении объекта."""

    DURATION = 22

    def __init__(self, x, y, color, count=9):
        """Создаёт частицы, разлетающиеся из точки в стороны.

        Args:
            x: координата центра эффекта по горизонтали.
            y: координата центра эффекта по вертикали.
            color: цвет частиц.
            count: количество частиц.
        """
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
        """Сдвигает частицы и гасит их скорость на один кадр."""
        self.timer += 1
        for p in self.particles:
            p[0] += p[2]
            p[1] += p[3]
            p[2] *= 0.86
            p[3] *= 0.86

    @property
    def progress(self):
        """Доля проигранного эффекта от 0.0 до 1.0."""
        return min(1.0, self.timer / self.DURATION)

    @property
    def is_done(self):
        """True, если эффект полностью отыграл."""
        return self.timer >= self.DURATION


class Obstacle:
    """Препятствие на карте (камень, дерево и т.п.)."""

    def __init__(self, x, y, width, height, asset, solid=True):
        """Создаёт препятствие с центром в точке (x, y).

        Args:
            x: координата центра по горизонтали.
            y: координата центра по вертикали.
            width: ширина в пикселях.
            height: высота в пикселях.
            asset: изображение для отрисовки.
            solid: True, если препятствие непроходимо.
        """
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.asset = asset
        self.solid = solid

    @property
    def rect(self):
        """Прямоугольник препятствия как (x, y, width, height)."""
        return (
            self.x - self.width / 2,
            self.y - self.height / 2,
            self.width,
            self.height,
        )


class Tower:
    """Башня игрока, которую защищают от врагов."""

    def __init__(self, x, y, size, max_hp, hitbox_size=None):
        """Создаёт башню в точке (x, y).

        Args:
            x: координата центра по горизонтали.
            y: координата центра по вертикали.
            size: визуальный размер башни.
            max_hp: максимальное и стартовое здоровье.
            hitbox_size: размер зоны попаданий (по умолчанию равен size).
        """
        self.x = x
        self.y = y
        self.size = size
        self.hitbox_size = hitbox_size or size
        self.hp = max_hp
        self.max_hp = max_hp

    def take_damage(self, amount):
        """Уменьшает здоровье башни, не опуская его ниже нуля.

        Args:
            amount: величина урона.
        """
        self.hp = max(0, self.hp - amount)

    @property
    def is_destroyed(self):
        """True, если здоровье башни упало до нуля."""
        return self.hp <= 0

    @property
    def hitbox_rect(self):
        """Прямоугольник зоны попаданий как (x, y, size, size)."""
        half = self.hitbox_size / 2
        return (self.x - half, self.y - half, self.hitbox_size, self.hitbox_size)


class Enemy:
    """Обычный враг, идущий к башне по построенному пути."""

    coin_value = 1

    def __init__(self, x, y, size, hp, speed, damage):
        """Создаёт врага в точке (x, y).

        Args:
            x: координата по горизонтали.
            y: координата по вертикали.
            size: размер врага.
            hp: здоровье врага.
            speed: скорость движения за кадр.
            damage: урон, наносимый башне.
        """
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
        """Двигает врага к следующей точке пути или к цели.

        Args:
            target_x: координата цели по горизонтали (запасная, если
                путь не задан).
            target_y: координата цели по вертикали.
        """
        next_x, next_y = self._next_target(target_x, target_y)
        dx = next_x - self.x
        dy = next_y - self.y
        dist = math.hypot(dx, dy)
        if dist != 0:
            if dist < self.speed:
                self.x = next_x
                self.y = next_y
                if self.path and self.path_index < len(self.path):
                    self.path_index += 1
            else:
                self.x += (dx / dist) * self.speed
                self.y += (dy / dist) * self.speed
        self.tick_status()

    def tick_status(self):
        """Обновляет вспышку от попадания и отдачу за кадр."""
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
        """Возвращает следующую точку пути или запасную цель.

        Args:
            fallback_x: запасная координата по горизонтали.
            fallback_y: запасная координата по вертикали.

        Returns:
            Кортеж (x, y) - куда двигаться дальше.
        """
        if self.path and self.path_index < len(self.path):
            return self.path[self.path_index]
        return fallback_x, fallback_y

    def distance_to(self, x, y):
        """Возвращает расстояние от врага до точки (x, y).

        Args:
            x: координата точки по горизонтали.
            y: координата точки по вертикали.

        Returns:
            Евклидово расстояние до точки.
        """
        return math.hypot(x - self.x, y - self.y)

    def take_damage(self, amount):
        """Уменьшает здоровье врага.

        Args:
            amount: величина урона.
        """
        self.hp -= amount

    @property
    def is_dead(self):
        """True, если здоровье врага упало до нуля или ниже."""
        return self.hp <= 0

    def act(self, engine):
        """Атакует башню при контакте и убирает себя из боя.

        Args:
            engine: игровой движок (объект GameEngine).
        """
        if engine.tower_contact(self):
            engine.damage_tower(self.damage)
            engine.enemies.remove(self)

    def on_hit(self):
        """Реакция на попадание снаряда (у обычного врага пустая)."""
        pass


class RangedEnemy(Enemy):
    """Дальнобойный враг, стреляющий по башне с дистанции."""

    coin_value = 2

    def __init__(
        self, x, y, size, hp, speed, damage, attack_range, fire_rate, initial_delay
    ):
        """Создаёт дальнобойного врага.

        Args:
            x: координата по горизонтали.
            y: координата по вертикали.
            size: размер врага.
            hp: здоровье врага.
            speed: скорость движения за кадр.
            damage: урон снаряда.
            attack_range: дистанция, с которой враг открывает огонь.
            fire_rate: перезарядка между выстрелами в кадрах.
            initial_delay: задержка перед первым выстрелом.
        """
        super().__init__(x, y, size, hp, speed, damage)
        self.attack_range = attack_range
        self.fire_rate = fire_rate
        self.fire_cooldown = initial_delay

    def move_towards(self, target_x, target_y):
        """Подходит к цели, но останавливается в радиусе атаки.

        Args:
            target_x: координата цели по горизонтали.
            target_y: координата цели по вертикали.
        """
        if self.distance_to(target_x, target_y) <= self.attack_range:
            self.tick_status()
            return
        super().move_towards(target_x, target_y)

    def can_fire(self):
        """Сообщает, завершена ли перезарядка и можно ли стрелять."""
        return self.fire_cooldown <= 0

    def reset_cooldown(self):
        """Сбрасывает перезарядку до полного значения fire_rate."""
        self.fire_cooldown = self.fire_rate

    def update_cooldown(self):
        """Уменьшает счётчик перезарядки на один кадр."""
        if self.fire_cooldown > 0:
            self.fire_cooldown -= 1

    def in_range(self, target_x, target_y):
        """Проверяет, находится ли цель в радиусе атаки.

        Args:
            target_x: координата цели по горизонтали.
            target_y: координата цели по вертикали.

        Returns:
            True, если цель в пределах attack_range, иначе False.
        """
        return self.distance_to(target_x, target_y) <= self.attack_range

    def act(self, engine):
        """Стреляет по башне, если та в радиусе и готова перезарядка.

        Args:
            engine: игровой движок (объект GameEngine).
        """
        if self.in_range(engine.tower.x, engine.tower.y):
            self.update_cooldown()
            if self.can_fire():
                engine.fire_enemy_projectile(self)
                self.reset_cooldown()

    def on_hit(self):
        """Сбрасывает перезарядку при попадании по врагу."""
        self.reset_cooldown()


class Coin:
    """Монета, выпадающая из врага и собираемая к башне."""

    _COLLECT_SPEED = 16

    def __init__(self, x, y, value, vx: float = 0, vy: float = 0, anim_phase=0):
        """Создаёт монету в точке (x, y).

        Args:
            x: координата по горизонтали.
            y: координата по вертикали.
            value: ценность монеты в монетах профиля.
            vx: начальная скорость разлёта по горизонтали.
            vy: начальная скорость разлёта по вертикали.
            anim_phase: стартовая фаза анимации покачивания.
        """
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
        self.pending_collect = False

    def start_collect(self, tx, ty, cx, cy):
        """Запускает полёт монеты к точке сбора по дуге Безье.

        Args:
            tx: конечная координата сбора по горизонтали.
            ty: конечная координата сбора по вертикали.
            cx: контрольная точка дуги по горизонтали.
            cy: контрольная точка дуги по вертикали.
        """
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
        """Обновляет состояние монеты на один кадр.

        В режиме сбора двигает монету по дуге к цели, иначе проигрывает
        разлёт с трением либо анимацию покачивания.
        """
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
        """True, пока монета ещё разлетается после выпадения."""
        return self.drop_timer > 0


class Projectile:
    """Снаряд, летящий по прямой с постоянной скоростью."""

    def __init__(self, x, y, vx, vy, speed, damage):
        """Создаёт снаряд в точке (x, y).

        Args:
            x: координата по горизонтали.
            y: координата по вертикали.
            vx: единичное направление по горизонтали.
            vy: единичное направление по вертикали.
            speed: скорость полёта за кадр.
            damage: наносимый урон.
        """
        self.x = x
        self.y = y
        self.vx = vx
        self.vy = vy
        self.speed = speed
        self.damage = damage

    def update(self):
        """Сдвигает снаряд по направлению на один кадр."""
        self.x += self.vx * self.speed
        self.y += self.vy * self.speed
