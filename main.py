import pygame
from config import GAME_CONFIG
from settings import load_settings
from scenes.menu_scene import MenuScene, SettingsScene
from scenes.game_scene import GameScene


class App:
    def __init__(self):
        pygame.init()
        self.settings = load_settings()
        self.width, self.height = self.settings["resolution"]
        self.screen = self._create_screen()
        pygame.display.set_caption("Tower Defense")
        self.clock = pygame.time.Clock()
        self.running = True
        self.scene = MenuScene(self.width, self.height)

    def _create_screen(self):
        flags = pygame.FULLSCREEN if self.settings["is_fullscreen"] else 0
        return pygame.display.set_mode((self.width, self.height), flags)

    def _apply_settings(self):
        self.settings = load_settings()
        self.width, self.height = self.settings["resolution"]
        self.screen = self._create_screen()
        self.scene = MenuScene(self.width, self.height)

    def run(self):
        while self.running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                    break
                result = self.scene.handle_event(event)
                self._handle_scene_result(result)

            self.scene.update()
            self.scene.draw(self.screen)
            pygame.display.flip()
            self.clock.tick(GAME_CONFIG["fps"])

        pygame.quit()

    def _handle_scene_result(self, result):
        if result == "quit":
            self.running = False
        elif result == "game":
            self.scene = GameScene(self.width, self.height)
        elif result == "menu":
            self.scene = MenuScene(self.width, self.height)
        elif result == "settings":
            self.scene = SettingsScene(self.width, self.height)
        elif result == "apply_settings":
            self._apply_settings()


if __name__ == "__main__":
    App().run()
