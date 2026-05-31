import pygame

from config import AVAILABLE_RESOLUTIONS, COLORS
from settings import load_settings, save_settings
from view.assets import AssetStore
from view.fonts import make_font
from view.widgets import Button


class _BaseMenuScene:
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.assets = AssetStore()

    def _texture_buttons(self, buttons):
        texture = self.assets.optional_image("tiles/tavern_planks.png")
        for button in buttons:
            button.texture = texture

    def _draw_background(self, surface):
        grass = self.assets.optional_image("tiles/grass.png")
        if grass is None:
            surface.fill(COLORS["bg"])
            return

        for y in range(0, self.height, grass.get_height()):
            for x in range(0, self.width, grass.get_width()):
                surface.blit(grass, (x, y))

        shade = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        shade.fill((20, 18, 12, 78))
        surface.blit(shade, (0, 0))


class MenuScene(_BaseMenuScene):
    def __init__(self, width, height):
        super().__init__(width, height)
        self.font = make_font(20)
        self.title_font = make_font(36)
        self._create_buttons()

    def _create_buttons(self):
        bw, bh = 220, 45
        cx = self.width // 2 - bw // 2
        cy = self.height // 2 - 60
        self.buttons = [
            Button((cx, cy, bw, bh), "Бесконечная игра", self.font),
            Button((cx, cy + 60, bw, bh), "Настройки", self.font),
            Button((cx, cy + 120, bw, bh), "Выход", self.font),
        ]
        self._texture_buttons(self.buttons)

    def handle_event(self, event):
        if event.type == pygame.MOUSEMOTION:
            for btn in self.buttons:
                btn.check_hover(event.pos)
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.buttons[0].is_clicked(event.pos):
                return "game"
            if self.buttons[1].is_clicked(event.pos):
                return "settings"
            if self.buttons[2].is_clicked(event.pos):
                return "quit"
        return None

    def update(self):
        pass

    def draw(self, surface):
        self._draw_background(surface)
        title_surf, title_rect = self.title_font.render(
            "Tavern Defense", COLORS["title_text"]
        )
        surface.blit(title_surf, (self.width // 2 - title_rect.width // 2, 60))
        for btn in self.buttons:
            btn.draw(surface)


class SettingsScene(_BaseMenuScene):
    def __init__(self, width, height):
        super().__init__(width, height)
        self.font = make_font(18)
        self.title_font = make_font(28)
        self.settings = load_settings()
        self.res_index = self._get_res_index()
        self._create_buttons()

    def _get_res_index(self):
        res = tuple(self.settings["resolution"])
        if res in AVAILABLE_RESOLUTIONS:
            return AVAILABLE_RESOLUTIONS.index(res)
        return 1

    def _create_buttons(self):
        cx = self.width // 2
        cy = self.height // 2 - 60
        bw = 260
        self.fullscreen_btn = Button(
            (cx - bw // 2, cy, bw, 40),
            self._fullscreen_text(),
            self.font,
        )
        row_y = cy + 60
        self.res_left = Button((cx - bw // 2, row_y, 40, 40), "<", self.font)
        self.res_right = Button((cx + bw // 2 - 40, row_y, 40, 40), ">", self.font)
        btn_w = (bw - 10) // 2
        row_actions = cy + 130
        self.apply_btn = Button(
            (cx - bw // 2, row_actions, btn_w, 40), "Применить", self.font
        )
        self.back_btn = Button(
            (cx - bw // 2 + btn_w + 10, row_actions, btn_w, 40), "Назад", self.font
        )
        self._texture_buttons(
            [
                self.fullscreen_btn,
                self.res_left,
                self.res_right,
                self.apply_btn,
                self.back_btn,
            ]
        )

    def _fullscreen_text(self):
        return (
            "Полный экран: Да"
            if self.settings["is_fullscreen"]
            else "Полный экран: Нет"
        )

    def _res_text(self):
        w, h = AVAILABLE_RESOLUTIONS[self.res_index]
        return f"{w}x{h}"

    def _res_enabled(self):
        return not self.settings["is_fullscreen"]

    def handle_event(self, event):
        if event.type == pygame.MOUSEMOTION:
            hover_btns = [self.fullscreen_btn, self.apply_btn, self.back_btn]
            if self._res_enabled():
                hover_btns += [self.res_left, self.res_right]
            for btn in hover_btns:
                btn.check_hover(event.pos)
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            pos = event.pos
            if self.fullscreen_btn.is_clicked(pos):
                self.settings["is_fullscreen"] = not self.settings["is_fullscreen"]
                self.fullscreen_btn.text = self._fullscreen_text()
            elif self._res_enabled() and self.res_left.is_clicked(pos):
                self.res_index = (self.res_index - 1) % len(AVAILABLE_RESOLUTIONS)
            elif self._res_enabled() and self.res_right.is_clicked(pos):
                self.res_index = (self.res_index + 1) % len(AVAILABLE_RESOLUTIONS)
            elif self.apply_btn.is_clicked(pos):
                self.settings["resolution"] = AVAILABLE_RESOLUTIONS[self.res_index]
                save_settings(self.settings)
                return "apply_settings"
            elif self.back_btn.is_clicked(pos):
                return "menu"
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            return "menu"
        return None

    def update(self):
        pass

    def draw(self, surface):
        self._draw_background(surface)
        title_surf, title_rect = self.title_font.render(
            "Настройки", COLORS["title_text"]
        )
        surface.blit(title_surf, (self.width // 2 - title_rect.width // 2, 40))
        self.fullscreen_btn.draw(surface)
        if self._res_enabled():
            self.res_left.draw(surface)
            self.res_right.draw(surface)
            res_surf, res_rect = self.font.render(
                self._res_text(), COLORS["button_text"]
            )
            rx = self.width // 2 - res_rect.width // 2
            ry = self.res_left.rect.centery - res_rect.height // 2
            surface.blit(res_surf, (rx, ry))
        self.apply_btn.draw(surface)
        self.back_btn.draw(surface)
