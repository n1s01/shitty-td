import tkinter as tk

from config import AVAILABLE_RESOLUTIONS
from storage.settings_storage import AppSettings, load_settings, save_settings
from ui.settings_screen import SettingsScreen
from ui.widgets import create_button_row
from ui.game_screen import GameScreen


class MainMenu(tk.Tk):
    def __init__(self):
        super().__init__()

        self.settings = load_settings()
        self.title("Tower Defense")
        self.geometry(self.format_resolution(self.settings.resolution))
        self.resizable(False, False)
        self.protocol("WM_DELETE_WINDOW", self.close_game)
        self.is_fullscreen = self.settings.is_fullscreen
        self.current_resolution = self.settings.resolution
        self.attributes("-fullscreen", self.is_fullscreen)
        self.now_screen = None
        self.render_start_page()
        self.show_on_start()

    def clear(self):
        if self.now_screen is not None:
            self.now_screen.destroy()

    def set_screen(self, screen):
        self.clear()
        self.now_screen = screen
        self.now_screen.pack(fill=tk.BOTH, expand=True)
        return self.now_screen

    def create_screen(self):
        return self.set_screen(tk.Frame(self))

    def show_on_start(self):
        """показывает окно поверх остальных при запуске"""

        self.focus_force()
        self.attributes("-topmost", True)
        self.update()
        self.attributes("-topmost", False)

    def format_resolution(self, resolution):
        width, height = resolution
        return f"{width}x{height}"

    def render_start_page(self):
        screen = self.create_screen()

        menu_bar = tk.Frame(screen)
        menu_bar.pack(side=tk.TOP, fill=tk.X)

        buttons = (
            (
                "Бесконечная игра",
                self.infinity_game,
            ),
            ("Настройки", self.open_settings),
            ("Выход", self.close_game),
        )

        create_button_row(menu_bar, buttons)

        empty_background = tk.Frame(screen)
        empty_background.pack(fill=tk.BOTH, expand=True)

    def open_settings(self):
        screen = SettingsScreen(
            self,
            is_fullscreen=self.is_fullscreen,
            current_resolution=self.format_resolution(self.current_resolution),
            format_resolution=self.format_resolution,
            on_back=self.render_start_page,
            on_apply=self.apply_settings,
        )
        self.set_screen(screen)

    def apply_settings(self, is_fullscreen, selected_resolution):
        self.is_fullscreen = is_fullscreen
        self.attributes("-fullscreen", self.is_fullscreen)

        for resolution in AVAILABLE_RESOLUTIONS:
            if selected_resolution == self.format_resolution(resolution):
                self.current_resolution = resolution
                if not self.is_fullscreen:
                    self.geometry(self.format_resolution(resolution))
                break

        self.settings = AppSettings(
            is_fullscreen=self.is_fullscreen,
            resolution=self.current_resolution,
        )
        save_settings(self.settings)
        self.update_idletasks()

    def infinity_game(self):
        width, height = self.current_resolution
        game_screen = GameScreen(
            master=self, width=width, height=height, on_back=self.render_start_page
        )
        self.set_screen(game_screen)

    def close_game(self):
        self.destroy()
