import math

import pygame

# python3.14 require _freetype not pygame.freetype
from pygame import _freetype  # type: ignore[attr-defined]

from config import COLORS
from core.game_engine import GameEngine
from core.models import RangedEnemy
from view.assets import AssetStore


def _make_font(size):
    _freetype.init()
    return _freetype.Font(None, size)


class GameScene:
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.engine = GameEngine(width, height)
        self.assets = AssetStore()
        self.font = _make_font(14)
        self.game_over_font = _make_font(48)

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if not self.engine.is_game_over:
                self.engine.shoot_at(event.pos[0], event.pos[1])
            return None
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            return "menu"
        return None

    def update(self):
        self.engine.update()

    def draw(self, surface):
        self._draw_background(surface)
        self._draw_obstacles(surface)
        self._draw_tower(surface)
        self._draw_enemies(surface)
        self._draw_projectiles(surface)
        self._draw_enemy_projectiles(surface)
        if self.engine.is_game_over:
            self._draw_game_over(surface)

    def _draw_background(self, surface):
        grass = self.assets.optional_image("tiles/grass.png")
        if grass is None:
            surface.fill(COLORS["bg"])
            return

        for y in range(0, self.height, grass.get_height()):
            for x in range(0, self.width, grass.get_width()):
                surface.blit(grass, (x, y))

        self._draw_tower_garden(surface)

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
        text_surf, text_rect = self.font.render(f"HP: {tower.hp}", COLORS["tower_text"])
        hitbox_half = tower.hitbox_size // 2
        surface.blit(
            text_surf,
            (int(tower.x) - text_rect.width // 2, int(tower.y) - hitbox_half - 22),
        )

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
                surface.blit(img, img.get_rect(center=pos))
            else:
                pygame.draw.circle(surface, COLORS["enemy_fill"], pos, r)
                pygame.draw.circle(surface, COLORS["enemy_outline"], pos, r, 2)
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

    def _draw_projectiles(self, surface):
        length = 12
        arrow = self.assets.optional_image("sprites/projectile_arrow.png")
        for projectile in self.engine.projectiles:
            start_x = int(projectile.x)
            start_y = int(projectile.y)
            if arrow is not None:
                angle = -math.degrees(math.atan2(projectile.vy, projectile.vx))
                rotated = pygame.transform.rotate(arrow, angle)
                surface.blit(rotated, rotated.get_rect(center=(start_x, start_y)))
            else:
                end_x = int(projectile.x - projectile.vx * length)
                end_y = int(projectile.y - projectile.vy * length)
                pygame.draw.line(
                    surface,
                    COLORS["projectile_fill"],
                    (start_x, start_y),
                    (end_x, end_y),
                    2,
                )

    def _draw_enemy_projectiles(self, surface):
        length = 10
        firebolt = self.assets.optional_image("sprites/projectile_firebolt.png")
        for proj in self.engine.enemy_projectiles:
            start_x = int(proj.x)
            start_y = int(proj.y)
            if firebolt is not None:
                surface.blit(firebolt, firebolt.get_rect(center=(start_x, start_y)))
            else:
                end_x = int(proj.x - proj.vx * length)
                end_y = int(proj.y - proj.vy * length)
                pygame.draw.line(
                    surface,
                    COLORS["enemy_projectile_fill"],
                    (start_x, start_y),
                    (end_x, end_y),
                    3,
                )

    def _draw_game_over(self, surface):
        text_surf, text_rect = self.game_over_font.render(
            "ИГРА ОКОНЧЕНА", COLORS["game_over_text"]
        )
        x = self.width // 2 - text_rect.width // 2
        y = self.height // 2 - text_rect.height // 2
        surface.blit(text_surf, (x, y))
