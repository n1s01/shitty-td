"""Виджеты интерфейса: кнопки с текстурой и наведением."""

import pygame

from config import COLORS


class Button:
    """Кнопка с текстом, реагирующая на наведение и клик."""

    def __init__(self, rect, text, font, texture=None):
        """Создаёт кнопку с заданными прямоугольником и текстом.

        Args:
            rect: прямоугольник кнопки (x, y, width, height).
            text: подпись на кнопке.
            font: шрифт для отрисовки текста.
            texture: текстура-плитка для фона или None.
        """
        self.rect = pygame.Rect(rect)
        self.text = text
        self.font = font
        self.texture = texture
        self.hovered = False

    def draw(self, surface):
        """Рисует кнопку с фоном, рамкой и подписью.

        Args:
            surface: поверхность, на которой рисуется кнопка.
        """
        if self.texture is not None:
            button_surface = pygame.Surface(self.rect.size, pygame.SRCALPHA)
            for y in range(0, self.rect.height, self.texture.get_height()):
                for x in range(0, self.rect.width, self.texture.get_width()):
                    button_surface.blit(self.texture, (x, y))
            overlay = pygame.Surface(self.rect.size, pygame.SRCALPHA)
            overlay.fill((255, 214, 130, 28) if self.hovered else (35, 20, 12, 18))
            button_surface.blit(overlay, (0, 0))
            surface.blit(button_surface, self.rect)
        else:
            color = COLORS["button_hover"] if self.hovered else COLORS["button_bg"]
            pygame.draw.rect(surface, color, self.rect, border_radius=4)
        pygame.draw.rect(surface, (48, 29, 21), self.rect, 3, border_radius=4)
        text_surf, text_rect = self.font.render(self.text, COLORS["button_text"])
        x = self.rect.centerx - text_rect.width // 2
        y = self.rect.centery - text_rect.height // 2
        surface.blit(text_surf, (x, y))

    def check_hover(self, pos):
        """Обновляет состояние наведения по позиции курсора.

        Args:
            pos: координаты курсора (x, y).
        """
        self.hovered = self.rect.collidepoint(pos)

    def is_clicked(self, pos):
        """Проверяет, попадает ли клик в кнопку.

        Args:
            pos: координаты клика (x, y).

        Returns:
            True, если точка внутри кнопки, иначе False.
        """
        return self.rect.collidepoint(pos)
