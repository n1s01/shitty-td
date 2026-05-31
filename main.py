import pygame

from config import GAME_CONFIG, LOGICAL_RESOLUTION
from scenes.game_scene import GameScene
from scenes.menu_scene import MenuScene, SettingsScene
from settings import load_settings


class App:
    def __init__(self):
        pygame.init()
        self.settings = load_settings()
        self.base_w, self.base_h = LOGICAL_RESOLUTION
        self.canvas = pygame.Surface((self.base_w, self.base_h))
        self.screen = self._create_screen()
        pygame.display.set_caption("Tower Defense")
        self.clock = pygame.time.Clock()
        self.running = True
        self.scene = MenuScene(self.base_w, self.base_h)

    def _create_screen(self):
        if self.settings["is_fullscreen"]:
            screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
        else:
            screen = pygame.display.set_mode(self.settings["resolution"])
        self.screen_w, self.screen_h = screen.get_size()
        self._compute_viewport()
        return screen

    def _compute_viewport(self):
        self.scale = min(self.screen_w / self.base_w, self.screen_h / self.base_h)
        self.view_w = int(self.base_w * self.scale)
        self.view_h = int(self.base_h * self.scale)
        self.offset_x = (self.screen_w - self.view_w) // 2
        self.offset_y = (self.screen_h - self.view_h) // 2

    def _screen_to_logical(self, pos):
        x = (pos[0] - self.offset_x) / self.scale
        y = (pos[1] - self.offset_y) / self.scale
        return (x, y)

    def _translate_event(self, event):
        if event.type in (
            pygame.MOUSEBUTTONDOWN,
            pygame.MOUSEBUTTONUP,
            pygame.MOUSEMOTION,
        ):
            new_pos = self._screen_to_logical(event.pos)
            return pygame.event.Event(event.type, {**event.dict, "pos": new_pos})
        return event

    def _apply_settings(self):
        self.settings = load_settings()
        self.screen = self._create_screen()
        self.scene = MenuScene(self.base_w, self.base_h)

    def run(self):
        while self.running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                    break
                result = self.scene.handle_event(self._translate_event(event))
                self._handle_scene_result(result)

            self.scene.update()
            self.scene.draw(self.canvas)
            self._present()
            self.clock.tick(GAME_CONFIG["fps"])

        pygame.quit()

    def _present(self):
        scaled = pygame.transform.scale(self.canvas, (self.view_w, self.view_h))
        self.screen.fill((0, 0, 0))
        self.screen.blit(scaled, (self.offset_x, self.offset_y))
        pygame.display.flip()

    def _handle_scene_result(self, result):
        if result == "quit":
            self.running = False
        elif result == "game":
            self.scene = GameScene(self.base_w, self.base_h)
        elif result == "menu":
            self.scene = MenuScene(self.base_w, self.base_h)
        elif result == "settings":
            self.scene = SettingsScene(self.base_w, self.base_h)
        elif result == "apply_settings":
            self._apply_settings()


if __name__ == "__main__":
    App().run()
