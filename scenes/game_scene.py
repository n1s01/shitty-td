import pygame
from pygame import _freetype
from config import COLORS, GAME_CONFIG
from core.game_engine import GameEngine


def _make_font(size):
    _freetype.init()
    return _freetype.Font(None, size)


class GameScene:
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.engine = GameEngine(width, height)
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
        surface.fill(COLORS["bg"])
        self._draw_tower(surface)
        self._draw_enemies(surface)
        self._draw_projectiles(surface)
        if self.engine.is_game_over:
            self._draw_game_over(surface)

    def _draw_tower(self, surface):
        tower = self.engine.tower
        half = tower.size // 2
        rect = pygame.Rect(int(tower.x) - half, int(tower.y) - half, tower.size, tower.size)
        pygame.draw.rect(surface, COLORS["tower_fill"], rect)
        pygame.draw.rect(surface, COLORS["tower_outline"], rect, 3)
        text_surf, text_rect = self.font.render(f"HP: {tower.hp}", COLORS["tower_text"])
        surface.blit(text_surf, (int(tower.x) - text_rect.width // 2, int(tower.y) - half - 20))

    def _draw_enemies(self, surface):
        for enemy in self.engine.enemies:
            pos = (int(enemy.x), int(enemy.y))
            r = enemy.size // 2
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
        pygame.draw.rect(surface, COLORS["enemy_hp_fg"], (x, y, int(bar_w * pct), bar_h))

    def _draw_projectiles(self, surface):
        size = GAME_CONFIG["projectile_size"]
        for proj in self.engine.projectiles:
            pygame.draw.circle(surface, COLORS["projectile_fill"], (int(proj.x), int(proj.y)), size)

    def _draw_game_over(self, surface):
        text_surf, text_rect = self.game_over_font.render("ИГРА ОКОНЧЕНА", COLORS["game_over_text"])
        x = self.width // 2 - text_rect.width // 2
        y = self.height // 2 - text_rect.height // 2
        surface.blit(text_surf, (x, y))
