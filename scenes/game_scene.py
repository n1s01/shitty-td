import math

import pygame

from config import COIN_CONFIG, COLORS, GAME_CONFIG
from core.game_engine import GameEngine
from core.map_generator import GRASS, SHORE, WATER
from core.models import RangedEnemy
from view.assets import AssetStore
from view.fonts import make_font

BIOME_FALLBACK = {
    WATER: (46, 116, 160),
    SHORE: (196, 178, 128),
    GRASS: (76, 128, 58),
}


class GameScene:
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.engine = GameEngine(width, height)
        self.assets = AssetStore()
        self.font = make_font(14)
        self.hud_font = make_font(20)
        self.balance_font = make_font(26)
        self.game_over_font = make_font(48)
        self.grass_tiles = [
            "tiles/grass_1.png",
            "tiles/grass_2.png",
            "tiles/grass_3.png",
            "tiles/grass_4.png",
        ]

        self._water_surface = None
        self._hud_tick = 0

    def _wave_button_rect(self):
        img = self.assets.optional_image("ui/wave_button.png")
        w = img.get_width() if img else 120
        h = img.get_height() if img else 36
        return pygame.Rect(self.width - w - 16, self.height - h - 16, w, h)

    def handle_event(self, event):
        if event.type == pygame.MOUSEMOTION:
            tx, ty = self._balance_coin_center()
            self.engine.collect_coin_at(event.pos[0], event.pos[1], tx, ty)
            return None
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.engine.wave_ready:
                if self._wave_button_rect().collidepoint(event.pos):
                    self.engine.start_wave()
                    return None
            if not self.engine.is_game_over:
                self.engine.shoot_at(event.pos[0], event.pos[1])
            return None
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            return "menu"
        return None

    def update(self):
        self.engine.update()
        self._hud_tick += 1

    def draw(self, surface):
        self._draw_background(surface)
        self._draw_obstacles(surface)
        self._draw_tower(surface)
        self._draw_enemies(surface)
        self._draw_projectile_list(
            surface,
            self.engine.projectiles,
            "sprites/projectile_arrow.png",
            COLORS["projectile_fill"],
            12,
        )
        self._draw_projectile_list(
            surface,
            self.engine.enemy_projectiles,
            "sprites/projectile_firebolt.png",
            COLORS["enemy_projectile_fill"],
            10,
        )
        self._draw_effects(surface)
        self._draw_coins(surface)
        self._draw_balance(surface)
        if self.engine.is_victory:
            self._draw_victory(surface)
        elif self.engine.is_game_over:
            self._draw_game_over(surface)
        else:
            self._draw_wave_button(surface)

    def _draw_background(self, surface):
        ts = self.engine.tile_size
        grass = [self.assets.optional_image(p) for p in self.grass_tiles]
        grass = [g for g in grass if g is not None]
        sand = self.assets.optional_image("tiles/sand.png")

        for row in range(self.engine.tile_rows):
            for col in range(self.engine.tile_cols):
                biome = self.engine.biome_map[row][col]
                if biome == WATER:
                    continue
                x, y = col * ts, row * ts
                img = self._tile_image(biome, col, row, grass, sand)
                if img is not None:
                    surface.blit(img, (x, y))
                else:
                    pygame.draw.rect(surface, BIOME_FALLBACK[biome], (x, y, ts, ts))

        if self._water_surface is None:
            self._water_surface = self._build_water_surface()
        surface.blit(self._water_surface, (0, 0))

        self._draw_decor(surface)
        self._draw_tower_garden(surface)

    def _tile_image(self, biome, col, row, grass, sand):
        if biome == SHORE:
            return sand
        if grass:
            return grass[_stable_noise(col, row, 5) % len(grass)]
        return None

    def _build_water_surface(self):
        from core.perlin_noise import PerlinNoise

        surf = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        flow = PerlinNoise()
        detail = PerlinNoise()
        ts = self.engine.tile_size

        deep = (30, 92, 138, 255)
        mid = (44, 118, 165, 255)
        light = (74, 152, 194, 255)
        shine = (140, 200, 222, 255)

        flow_scale = 0.05
        detail_scale = 0.14
        step = 8

        for row in range(self.engine.tile_rows):
            for col in range(self.engine.tile_cols):
                if self.engine.biome_map[row][col] != WATER:
                    continue
                x0, y0 = col * ts, row * ts
                for y in range(y0, y0 + ts, step):
                    for x in range(x0, x0 + ts, step):
                        sx, sy = x + step / 2, y + step / 2
                        v = flow.fractal_noise2d(
                            sx * flow_scale, sy * flow_scale, octaves=2
                        )
                        d = detail.noise2d(sx * detail_scale, sy * detail_scale)
                        val = v + 0.35 * d
                        if val > 0.55:
                            c = shine
                        elif val > 0.18:
                            c = light
                        elif val > -0.3:
                            c = mid
                        else:
                            c = deep
                        surf.fill(c, (x, y, step, step))
        return surf

    def _draw_decor(self, surface):
        for item in self.engine.decor:
            img = self.assets.optional_image(item["asset"])
            if img is None:
                continue
            rect = img.get_rect(center=(int(item["x"]), int(item["y"])))
            surface.blit(img, rect)

    def _draw_tower_garden(self, surface):
        tower = self.engine.tower
        garden = pygame.Rect(0, 0, tower.hitbox_size, tower.hitbox_size)
        garden.center = (int(tower.x), int(tower.y))
        soil = self.assets.optional_image("tiles/tilled_soil.png")
        if soil is not None:
            for y in range(garden.top, garden.bottom, soil.get_height()):
                for x in range(garden.left, garden.right, soil.get_width()):
                    source = pygame.Rect(0, 0, soil.get_width(), soil.get_height())
                    target = pygame.Rect(x, y, soil.get_width(), soil.get_height())
                    clipped = target.clip(garden)
                    source.size = clipped.size
                    source.topleft = (0, 0)
                    surface.blit(soil, clipped, source)
        else:
            pygame.draw.rect(surface, (86, 55, 34), garden)
        self._draw_garden_fence(surface, garden)

    def _draw_garden_fence(self, surface, garden):
        rail_dark = (52, 31, 22)
        rail_mid = (107, 66, 37)
        rail_light = (157, 103, 52)
        post_dark = (45, 27, 20)
        post_mid = (119, 72, 39)

        pygame.draw.rect(surface, rail_dark, garden, 5)
        pygame.draw.line(surface, rail_mid, garden.topleft, garden.topright, 3)
        pygame.draw.line(surface, rail_mid, garden.bottomleft, garden.bottomright, 3)
        pygame.draw.line(surface, rail_mid, garden.topleft, garden.bottomleft, 3)
        pygame.draw.line(surface, rail_mid, garden.topright, garden.bottomright, 3)

        for x in range(garden.left, garden.right + 1, 32):
            self._draw_fence_post(
                surface, x, garden.top, post_dark, post_mid, rail_light
            )
            self._draw_fence_post(
                surface, x, garden.bottom, post_dark, post_mid, rail_light
            )
        for y in range(garden.top, garden.bottom + 1, 32):
            self._draw_fence_post(
                surface, garden.left, y, post_dark, post_mid, rail_light
            )
            self._draw_fence_post(
                surface, garden.right, y, post_dark, post_mid, rail_light
            )

    def _draw_fence_post(self, surface, x, y, dark, mid, light):
        rect = pygame.Rect(0, 0, 10, 14)
        rect.center = (x, y)
        pygame.draw.rect(surface, dark, rect)
        pygame.draw.rect(surface, mid, rect.inflate(-3, -3))
        pygame.draw.rect(surface, light, (rect.left + 3, rect.top + 2, 3, 2))

    def _draw_obstacles(self, surface):
        for obstacle in self.engine.obstacles:
            img = self.assets.optional_image(
                obstacle.asset, (int(obstacle.width), int(obstacle.height))
            )
            rect = pygame.Rect(0, 0, int(obstacle.width), int(obstacle.height))
            rect.center = (int(obstacle.x), int(obstacle.y))
            if img is not None:
                surface.blit(img, rect)
            else:
                pygame.draw.rect(surface, (81, 69, 45), rect)

    def _draw_tower(self, surface):
        tower = self.engine.tower
        half = tower.size // 2
        rect = pygame.Rect(
            int(tower.x) - half, int(tower.y) - half, tower.size, tower.size
        )
        img = self.assets.optional_image(
            "sprites/tavern_tower.png", (tower.size + 18, tower.size + 18)
        )
        if img is not None:
            img_rect = img.get_rect(center=(int(tower.x), int(tower.y)))
            surface.blit(img, img_rect)
        else:
            pygame.draw.rect(surface, COLORS["tower_fill"], rect)
            pygame.draw.rect(surface, COLORS["tower_outline"], rect, 3)
        self._draw_tower_keeper(surface)
        self._draw_tower_hp(surface)

    def _draw_tower_hp(self, surface):
        tower = self.engine.tower
        bar_w, bar_h = 140, 18
        cx = int(tower.x)
        top = int(tower.y) - tower.hitbox_size // 2 - 32
        panel = pygame.Rect(cx - bar_w // 2, top, bar_w, bar_h)

        # Деревянная рамка в стиле таверны
        pygame.draw.rect(surface, (44, 26, 14), panel, border_radius=6)
        track = panel.inflate(-6, -6)
        pygame.draw.rect(surface, (28, 16, 9), track, border_radius=4)

        # Заливка здоровья: зелёная -> жёлтая -> красная
        pct = tower.hp / tower.max_hp
        if pct > 0.5:
            fill_color = (96, 184, 88)
        elif pct > 0.25:
            fill_color = (224, 176, 56)
        else:
            fill_color = (208, 72, 56)

        fill_w = int(track.width * pct)
        if fill_w > 0:
            fill = pygame.Rect(track.left, track.top, fill_w, track.height)
            pygame.draw.rect(surface, fill_color, fill, border_radius=4)
            highlight = pygame.Rect(
                track.left, track.top, fill_w, max(1, track.height // 3)
            )
            light = tuple(min(255, c + 45) for c in fill_color)
            pygame.draw.rect(surface, light, highlight, border_radius=4)

        pygame.draw.rect(surface, (138, 92, 50), panel, width=2, border_radius=6)

        # Текст с лёгкой тенью для читаемости
        label = f"{tower.hp} / {tower.max_hp}"
        shadow, _ = self.font.render(label, (20, 12, 6))
        text_surf, text_rect = self.font.render(label, (255, 246, 222))
        tx = cx - text_rect.width // 2
        ty = panel.centery - text_rect.height // 2
        surface.blit(shadow, (tx + 1, ty + 1))
        surface.blit(text_surf, (tx, ty))

        self._draw_reload_bar(surface, panel)

    def _draw_reload_bar(self, surface, hp_panel):
        progress = self.engine.reload_progress
        if progress >= 1.0:
            return
        bar = pygame.Rect(
            hp_panel.left + 6, hp_panel.bottom + 3, hp_panel.width - 12, 4
        )
        pygame.draw.rect(surface, (28, 16, 9), bar, border_radius=2)
        fill_w = int(bar.width * progress)
        if fill_w > 0:
            pygame.draw.rect(
                surface,
                (210, 190, 120),
                (bar.left, bar.top, fill_w, bar.height),
                border_radius=2,
            )

    def _draw_tower_keeper(self, surface):
        timer = self.engine.tower_shoot_timer
        anim_frames = GAME_CONFIG["tower_shoot_anim_frames"]
        if timer <= 0:
            asset = "sprites/tower_keeper_idle.png"
        elif timer > anim_frames * 0.45:
            asset = "sprites/tower_keeper_shoot_1.png"
        else:
            asset = "sprites/tower_keeper_shoot_2.png"

        keeper = self.assets.optional_image(asset, (38, 38))
        if keeper is None:
            return

        if self.engine.tower_last_shot_dir[0] > 0:
            keeper = pygame.transform.flip(keeper, True, False)
        tower = self.engine.tower
        recoil = 2 if 0 < timer <= anim_frames * 0.45 else 0
        recoil_x = int(-self.engine.tower_last_shot_dir[0] * recoil)
        rect = keeper.get_rect(center=(int(tower.x) + recoil_x, int(tower.y) - 22))
        surface.blit(keeper, rect)

    def _draw_enemies(self, surface):
        for enemy in self.engine.enemies:
            pos = (int(enemy.x), int(enemy.y))
            r = enemy.size // 2
            asset = (
                "sprites/enemy_ranged.png"
                if isinstance(enemy, RangedEnemy)
                else "sprites/enemy_raider.png"
            )
            img = self.assets.optional_image(asset, (enemy.size + 14, enemy.size + 14))
            if img is not None:
                if enemy.hit_flash_time > 0:
                    t = enemy.hit_flash_time / GAME_CONFIG["hit_flash_frames"]
                    gb = int(255 * (1 - t * 0.75))
                    tinted = img.copy()
                    tinted.fill(
                        (255, gb, gb, 255), special_flags=pygame.BLEND_RGBA_MULT
                    )
                    surface.blit(tinted, tinted.get_rect(center=pos))
                else:
                    surface.blit(img, img.get_rect(center=pos))
            else:
                color = (
                    (220, 60, 60) if enemy.hit_flash_time > 0 else COLORS["enemy_fill"]
                )
                pygame.draw.circle(surface, color, pos, r)
                pygame.draw.circle(surface, COLORS["enemy_outline"], pos, r, 2)
            if isinstance(enemy, RangedEnemy):
                pygame.draw.circle(surface, (180, 100, 220), pos, enemy.attack_range, 1)
            if enemy.hp < enemy.max_hp:
                self._draw_enemy_hp(surface, enemy, r)

    def _draw_enemy_hp(self, surface, enemy, r):
        bar_w = enemy.size
        bar_h = 4
        x = int(enemy.x) - bar_w // 2
        y = int(enemy.y) - r - 8
        pygame.draw.rect(surface, COLORS["enemy_hp_bg"], (x, y, bar_w, bar_h))
        pct = enemy.hp / enemy.max_hp
        pygame.draw.rect(
            surface, COLORS["enemy_hp_fg"], (x, y, int(bar_w * pct), bar_h)
        )

    def _draw_projectile_list(
        self, surface, projectiles, sprite_key, fallback_color, tail_length
    ):
        sprite = self.assets.optional_image(sprite_key)
        for proj in projectiles:
            cx, cy = int(proj.x), int(proj.y)
            if sprite is not None:
                angle = -math.degrees(math.atan2(proj.vy, proj.vx))
                rotated = pygame.transform.rotate(sprite, angle)
                surface.blit(rotated, rotated.get_rect(center=(cx, cy)))
            else:
                end_x = int(proj.x - proj.vx * tail_length)
                end_y = int(proj.y - proj.vy * tail_length)
                pygame.draw.line(surface, fallback_color, (cx, cy), (end_x, end_y), 2)

    def _draw_effects(self, surface):
        for effect in self.engine.effects:
            fade = 1.0 - effect.progress
            size = max(1, int(4 * fade) + 1)
            base = effect.color

            c = (
                int(base[0] * fade + 24),
                int(base[1] * fade + 18),
                int(base[2] * fade + 12),
            )
            for p in effect.particles:
                rect = (int(p[0]) - size // 2, int(p[1]) - size // 2, size, size)
                pygame.draw.rect(surface, c, rect)

    _BALANCE_POS = (16, 14)
    _BALANCE_ICON = 22
    _BALANCE_PAD = 9
    _BALANCE_H = 40

    def _balance_coin_center(self):
        x, y = self._BALANCE_POS
        return x + self._BALANCE_PAD + self._BALANCE_ICON // 2, y + self._BALANCE_H // 2

    def _draw_coins(self, surface):
        r = COIN_CONFIG["size"]
        color = COIN_CONFIG["color"]
        img_base = self.assets.optional_image("sprites/coin.png", (r * 2, r * 2))
        for coin in self.engine.coins:
            cx, cy = int(coin.x), int(coin.y)
            if coin.collecting or coin.is_dropping:
                if img_base is not None:
                    surface.blit(img_base, img_base.get_rect(center=(cx, cy)))
                else:
                    self._draw_coin_shape(surface, cx, cy, r * 2, r * 2, color)
            else:
                self._draw_spinning_coin(surface, cx, cy, r, coin.anim_tick)

    def _draw_spinning_coin(self, surface, cx, cy, base_r, tick, shadow=True):
        color = COIN_CONFIG["color"]
        d = base_r * 2
        img_base = self.assets.optional_image("sprites/coin.png", (d, d))
        cy += int(2 * math.sin(tick * 0.09))
        spin_w = max(int(base_r * 0.8), int(d * abs(math.cos(tick * 0.055))))
        if img_base is not None:
            if shadow:
                shadow_r = pygame.Rect(0, 0, spin_w + 2, d + 2)
                shadow_r.center = (cx + 2, cy + 3)
                pygame.draw.ellipse(surface, (30, 30, 20), shadow_r)
            img = (
                pygame.transform.scale(img_base, (spin_w, d))
                if spin_w != d
                else img_base
            )
            surface.blit(img, img.get_rect(center=(cx, cy)))
        else:
            self._draw_coin_shape(surface, cx, cy, spin_w, d, color)

    def _draw_coin_shape(self, surface, cx, cy, w, h, color):
        shadow = pygame.Rect(0, 0, w + 2, h + 2)
        shadow.center = (cx + 2, cy + 3)
        pygame.draw.ellipse(surface, (30, 30, 20), shadow)
        outline = pygame.Rect(0, 0, w + 2, h + 2)
        outline.center = (cx, cy)
        pygame.draw.ellipse(surface, (60, 40, 0), outline)
        body = pygame.Rect(0, 0, w, h)
        body.center = (cx, cy)
        pygame.draw.ellipse(surface, color, body)
        if w > 4:
            hi = pygame.Rect(0, 0, max(2, w // 3), max(2, h // 3))
            hi.center = (cx - w // 5, cy - h // 4)
            pygame.draw.ellipse(surface, (255, 248, 160), hi)

    def _draw_balance(self, surface):
        x, y = self._BALANCE_POS
        icon = self._BALANCE_ICON
        pad = self._BALANCE_PAD
        height = self._BALANCE_H
        gap = 7

        text_surf, text_rect = self.balance_font.render(
            str(self.engine.balance), (244, 222, 150)
        )
        width = pad + icon + gap + text_rect.width + pad
        panel = pygame.Rect(x, y, width, height)

        pygame.draw.rect(surface, (44, 26, 14), panel, border_radius=9)
        inner = panel.inflate(-4, -4)
        pygame.draw.rect(surface, (96, 60, 33), inner, border_radius=7)
        pygame.draw.rect(surface, (138, 92, 50), inner, width=2, border_radius=7)
        pygame.draw.line(
            surface,
            (122, 80, 44),
            (inner.left + 3, inner.top + 2),
            (inner.right - 3, inner.top + 2),
            1,
        )

        icon_x = x + pad
        coin_cx = icon_x + icon // 2
        coin_cy = y + height // 2
        self._draw_spinning_coin(
            surface, coin_cx, coin_cy, icon // 2, self._hud_tick, shadow=False
        )

        text_x = icon_x + icon + gap
        surface.blit(text_surf, (text_x, y + (height - text_rect.height) // 2))

    def _draw_wave_button(self, surface):
        rect = self._wave_button_rect()
        active = self.engine.wave_ready
        alpha = 255 if active else 110
        progress = self.engine.wave_progress

        img = self.assets.optional_image("ui/wave_button.png")
        if img is not None:
            btn = img.copy()
            btn.set_alpha(alpha)
            surface.blit(btn, rect)
        else:
            overlay = pygame.Surface(rect.size, pygame.SRCALPHA)
            overlay.fill((88, 52, 28, alpha))
            surface.blit(overlay, rect)
            pygame.draw.rect(surface, (148, 98, 54), rect, 2)

        fill_w = int(rect.width * progress)
        if fill_w > 0:
            fill = pygame.Surface((fill_w, rect.height), pygame.SRCALPHA)
            fill.fill((200, 170, 60, 60 if active else 45))
            surface.blit(fill, rect.topleft)

        wave_num = self.engine.wave_index + 1
        label = f"Волна {wave_num}"
        text_color = (235, 210, 130) if active else (160, 140, 90)
        text_surf, text_rect = self.font.render(label, text_color)
        tx = rect.centerx - text_rect.width // 2
        ty = rect.centery - text_rect.height // 2
        surface.blit(text_surf, (tx, ty))

    def _draw_victory(self, surface):
        text_surf, text_rect = self.game_over_font.render("ПОБЕДА!", (255, 220, 60))
        x = self.width // 2 - text_rect.width // 2
        y = self.height // 2 - text_rect.height // 2
        surface.blit(text_surf, (x, y))

    def _draw_game_over(self, surface):
        text_surf, text_rect = self.game_over_font.render(
            "ИГРА ОКОНЧЕНА", COLORS["game_over_text"]
        )
        x = self.width // 2 - text_rect.width // 2
        y = self.height // 2 - text_rect.height // 2
        surface.blit(text_surf, (x, y))


def _stable_noise(x, y, salt):
    value = x * 734287 + y * 912931 + salt * 19349663
    value = (value ^ (value >> 13)) * 1274126177
    return (value ^ (value >> 16)) & 0xFFFFFFFF
