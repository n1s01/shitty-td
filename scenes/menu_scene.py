import pygame

from config import AVAILABLE_RESOLUTIONS, COLORS
from settings import load_settings, save_settings
from view.assets import AssetStore
from view.fonts import make_pixel_font
from view.widgets import Button


class _BaseMenuScene:
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.assets = AssetStore()
        self._background = None

    def _texture_buttons(self, buttons):
        texture = self.assets.optional_image("tiles/tavern_planks.png")
        for button in buttons:
            button.texture = texture

    def _draw_background(self, surface):
        if self._background is None:
            self._background = self._build_background()
        surface.blit(self._background, (0, 0))

    def _build_background(self):
        canvas = pygame.Surface((self.width, self.height))
        image = self.assets.optional_image("ui/menu_background.png")
        if image is not None:
            self._blit_cover(canvas, image)
        else:
            self._blit_grass(canvas)
        return canvas

    def _blit_cover(self, canvas, image):
        img_w, img_h = image.get_size()
        scale = max(self.width / img_w, self.height / img_h)
        new_size = (round(img_w * scale), round(img_h * scale))
        scaled = pygame.transform.smoothscale(image, new_size)
        x = (self.width - new_size[0]) // 2
        y = (self.height - new_size[1]) // 2
        canvas.blit(scaled, (x, y))

    def _blit_grass(self, canvas):
        grass = self.assets.optional_image("tiles/grass.png")
        if grass is None:
            canvas.fill(COLORS["bg"])
            return
        for y in range(0, self.height, grass.get_height()):
            for x in range(0, self.width, grass.get_width()):
                canvas.blit(grass, (x, y))


class MenuScene(_BaseMenuScene):
    def __init__(self, width, height):
        super().__init__(width, height)
        self.font = make_pixel_font(24)
        self.title_font = make_pixel_font(48)
        self.margin_x = 150
        self.title_y = height // 2 - 160
        self._create_buttons()

    def _create_buttons(self):
        bw, bh = 260, 52
        x = self.margin_x
        y = self.height // 2 - 20
        gap = 72
        self.buttons = [
            Button((x, y, bw, bh), "Бесконечная игра", self.font),
            Button((x, y + gap, bw, bh), "Настройки", self.font),
            Button((x, y + 2 * gap, bw, bh), "Выход", self.font),
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
        self._draw_title(surface)
        for btn in self.buttons:
            btn.draw(surface)

    def _draw_title(self, surface):
        title = "Tavern Defense"
        x, y = self.margin_x, self.title_y
        shadow, _ = self.title_font.render(title, (38, 22, 12))
        main, _ = self.title_font.render(title, (245, 222, 150))
        surface.blit(shadow, (x + 3, y + 3))
        surface.blit(main, (x, y))


class SettingsScene(_BaseMenuScene):
    def __init__(self, width, height):
        super().__init__(width, height)
        self.font = make_pixel_font(20)
        self.title_font = make_pixel_font(34)
        self.margin_x = 150
        self.panel_w = 300
        self.title_y = height // 2 - 160
        self.settings = load_settings()
        self.res_index = self._get_res_index()
        self._create_buttons()

    def _get_res_index(self):
        res = tuple(self.settings["resolution"])
        if res in AVAILABLE_RESOLUTIONS:
            return AVAILABLE_RESOLUTIONS.index(res)
        return 1

    def _create_buttons(self):
        x = self.margin_x
        bw = self.panel_w
        bh = 48
        y = self.height // 2 - 40
        self.fullscreen_btn = Button(
            (x, y, bw, bh),
            self._fullscreen_text(),
            self.font,
        )
        row_y = y + 64
        self.res_left = Button((x, row_y, 48, bh), "<", self.font)
        self.res_right = Button((x + bw - 48, row_y, 48, bh), ">", self.font)
        btn_w = (bw - 12) // 2
        row_actions = row_y + 80
        self.back_btn = Button((x, row_actions, btn_w, bh), "Назад", self.font)
        self.apply_btn = Button(
            (x + btn_w + 12, row_actions, btn_w, bh), "Применить", self.font
        )
        self._texture_buttons(
            [
                self.fullscreen_btn,
                self.res_left,
                self.res_right,
                self.back_btn,
                self.apply_btn,
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
            hover_btns = [self.fullscreen_btn, self.back_btn, self.apply_btn]
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
        self._draw_title(surface)
        self.fullscreen_btn.draw(surface)
        if self._res_enabled():
            self.res_left.draw(surface)
            self.res_right.draw(surface)
            res_surf, res_rect = self.font.render(
                self._res_text(), COLORS["button_text"]
            )
            rx = self.margin_x + self.panel_w // 2 - res_rect.width // 2
            ry = self.res_left.rect.centery - res_rect.height // 2
            surface.blit(res_surf, (rx, ry))
        self.back_btn.draw(surface)
        self.apply_btn.draw(surface)

    def _draw_title(self, surface):
        title = "Настройки"
        x, y = self.margin_x, self.title_y
        shadow, _ = self.title_font.render(title, (38, 22, 12))
        main, _ = self.title_font.render(title, (245, 222, 150))
        surface.blit(shadow, (x + 3, y + 3))
        surface.blit(main, (x, y))
