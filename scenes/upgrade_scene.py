"""Сцена прокачки: покупка улучшений за накопленные монеты."""

import pygame

from config import UPGRADES
from core import upgrades
from core.profile import load_profile, save_profile
from scenes.menu_scene import _BaseMenuScene
from view.fonts import make_ui_font
from view.widgets import Button

CARD_W, CARD_H = 360, 150
TAVERN_W, TAVERN_H = 440, 160


class UpgradeScene(_BaseMenuScene):
    """Экран улучшений с карточками апгрейдов и кнопкой назад."""

    def __init__(self, width, height):
        """Загружает профиль, готовит шрифты и раскладку карточек.

        Args:
            width: ширина экрана в пикселях.
            height: высота экрана в пикселях.
        """
        super().__init__(width, height)
        self.profile = load_profile()
        self.title_font = make_ui_font(46)
        self.card_font = make_ui_font(26)
        self.small_font = make_ui_font(20)
        self._mouse = (0, 0)
        self.cards = self._layout()
        self.back_btn = Button(
            (width // 2 - 150, height - 120, 300, 56), "Назад", self.card_font
        )
        self._texture_buttons([self.back_btn])

    def _layout(self):
        """Рассчитывает прямоугольники карточек улучшений.

        Returns:
            Словарь {uid: pygame.Rect} с расположением карточек.
        """
        side_ids = [u for u, s in UPGRADES.items() if s["kind"] == "side"]
        gap = 32
        total = len(side_ids) * CARD_W + (len(side_ids) - 1) * gap
        start_x = (self.width - total) // 2
        row_y = self.height // 2 - 230
        cards = {}
        for i, uid in enumerate(side_ids):
            x = start_x + i * (CARD_W + gap)
            cards[uid] = pygame.Rect(x, row_y, CARD_W, CARD_H)
        tx = (self.width - TAVERN_W) // 2
        ty = row_y + CARD_H + 160
        cards["tavern"] = pygame.Rect(tx, ty, TAVERN_W, TAVERN_H)
        return cards

    def handle_event(self, event):
        """Обрабатывает наведение, покупку улучшений и выход.

        Args:
            event: событие pygame.

        Returns:
            "menu" для возврата в главное меню или None.
        """
        if event.type == pygame.MOUSEMOTION:
            self._mouse = event.pos
            self.back_btn.check_hover(event.pos)
            return None
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.back_btn.is_clicked(event.pos):
                return "menu"
            for uid, rect in self.cards.items():
                if rect.collidepoint(event.pos) and upgrades.buy(self.profile, uid):
                    save_profile(self.profile)
            return None
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            return "menu"
        return None

    def update(self):
        """Обновляет состояние сцены (на экране прокачки ничего не меняется)."""
        pass

    def draw(self, surface):
        """Рисует фон, заголовок, баланс, связи и карточки улучшений.

        Args:
            surface: поверхность для отрисовки.
        """
        self._draw_background(surface)
        self._draw_title(surface)
        self._draw_balance(surface)
        self._draw_links(surface)
        for uid, rect in self.cards.items():
            self._draw_card(surface, uid, rect)
        self.back_btn.draw(surface)

    def _draw_title(self, surface):
        """Рисует заголовок «Прокачка» с тенью.

        Args:
            surface: поверхность для отрисовки.
        """
        shadow, _ = self.title_font.render("Прокачка", (38, 22, 12))
        main, trect = self.title_font.render("Прокачка", (245, 222, 150))
        x = self.width // 2 - trect.width // 2
        surface.blit(shadow, (x + 3, 63))
        surface.blit(main, (x, 60))

    def _draw_balance(self, surface):
        """Рисует текущий баланс монет игрока.

        Args:
            surface: поверхность для отрисовки.
        """
        label = f"Баланс: {self.profile['coins']}"
        shadow, _ = self.card_font.render(label, (20, 12, 6))
        main, trect = self.card_font.render(label, (255, 215, 80))
        x = self.width // 2 - trect.width // 2
        surface.blit(shadow, (x + 2, 132))
        surface.blit(main, (x, 130))

    def _draw_links(self, surface):
        """Рисует линии от побочных улучшений к главному (таверне).

        Args:
            surface: поверхность для отрисовки.
        """
        tavern = self.cards["tavern"]
        top = (tavern.centerx, tavern.top)
        unlocked = upgrades.is_unlocked(self.profile, "tavern")
        color = (150, 110, 60) if unlocked else (70, 60, 50)
        for uid, rect in self.cards.items():
            if uid == "tavern":
                continue
            pygame.draw.line(surface, color, (rect.centerx, rect.bottom), top, 3)

    def _draw_card(self, surface, uid, rect):
        """Рисует карточку улучшения с учётом её состояния.

        Args:
            surface: поверхность для отрисовки.
            uid: идентификатор улучшения.
            rect: прямоугольник карточки.
        """
        spec = UPGRADES[uid]
        maxed = upgrades.is_maxed(self.profile, uid)
        unlocked = upgrades.is_unlocked(self.profile, uid)
        affordable = self.profile["coins"] >= spec["cost"]
        hovered = rect.collidepoint(self._mouse)

        if not unlocked:
            border, fill = (70, 60, 50), (40, 34, 28)
        elif maxed:
            border, fill = (120, 170, 90), (40, 60, 34)
        elif hovered and affordable:
            border, fill = (210, 170, 90), (110, 72, 38)
        else:
            border, fill = (138, 92, 50), (78, 50, 28)

        pygame.draw.rect(surface, (28, 18, 10), rect, border_radius=10)
        pygame.draw.rect(surface, fill, rect.inflate(-6, -6), border_radius=8)
        pygame.draw.rect(surface, border, rect, width=3, border_radius=10)

        self._blit_text(
            surface,
            self.card_font,
            spec["title"],
            (245, 222, 150),
            rect.left + 16,
            rect.top + 14,
        )
        self._blit_text(
            surface,
            self.small_font,
            spec["desc"],
            (210, 196, 170),
            rect.left + 16,
            rect.top + 50,
        )
        self._draw_card_status(surface, uid, spec, rect, maxed, unlocked, affordable)

    def _draw_card_status(self, surface, uid, spec, rect, maxed, unlocked, affordable):
        """Рисует строку статуса карточки (цена, «Куплено» и т.п.).

        Args:
            surface: поверхность для отрисовки.
            uid: идентификатор улучшения.
            spec: словарь параметров улучшения.
            rect: прямоугольник карточки.
            maxed: True, если улучшение прокачано до максимума.
            unlocked: True, если улучшение разблокировано.
            affordable: True, если у игрока хватает монет.
        """
        if maxed:
            text, color = "Куплено", (150, 210, 120)
        elif not unlocked:
            text, color = "Открой все улучшения", (170, 150, 130)
        else:
            text = f"{spec['cost']} монет"
            color = (255, 215, 80) if affordable else (210, 100, 80)
        self._blit_text(
            surface, self.card_font, text, color, rect.left + 16, rect.bottom - 38
        )

    def _blit_text(self, surface, font, text, color, x, y):
        """Отрисовывает строку текста в заданной точке.

        Args:
            surface: поверхность для отрисовки.
            font: шрифт для рендеринга.
            text: текст для вывода.
            color: цвет текста.
            x: координата по горизонтали.
            y: координата по вертикали.
        """
        text_surf, _ = font.render(text, color)
        surface.blit(text_surf, (x, y))
