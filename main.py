import tkinter as tk

from config import AVAILABLE_RESOLUTIONS, BASE_RESOLUTION

WINDOW_MODES = ("Оконный", "Полный экран")
# 0 - оконный, 1 - полный экран


class MainMenu(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title("Tower Defense")
        self.geometry(self.format_resolution(BASE_RESOLUTION))
        self.resizable(False, False)
        self.protocol("WM_DELETE_WINDOW", self.close_game)
        self.is_fullscreen = False
        self.current_resolution = self.format_resolution(BASE_RESOLUTION)
        self.now_screen = None
        self.render_start_page()
        self.show_on_start()

    def clear(self):
        if self.now_screen is not None:
            self.now_screen.destroy()

    def create_screen(self):
        self.clear()
        self.now_screen = tk.Frame(self)
        self.now_screen.pack(fill=tk.BOTH, expand=True)
        return self.now_screen

    def show_on_start(self):
        """нужна что бы показывать сразу поверх всех окон и не нужно было через док ее раскрывать"""

        self.focus_force()
        self.attributes("-topmost", True)
        self.update()
        self.attributes("-topmost", False)

    def create_button_row(self, parent, buttons):
        buttons_frame = tk.Frame(parent)
        buttons_frame.pack()

        for text, command in buttons:
            button = tk.Button(buttons_frame, text=text, command=command)
            button.pack(side=tk.LEFT, padx=4, pady=4)

        return buttons_frame

    def create_option_row(self, parent, label_text, variable, options, command=None):
        row = tk.Frame(parent)
        row.pack(pady=10)

        label = tk.Label(row, text=label_text)
        label.pack(side=tk.LEFT, padx=5)

        menu = tk.OptionMenu(row, variable, *options, command=command)
        menu.pack(side=tk.LEFT, padx=5)

        return row, menu

    def format_resolution(self, resolution):
        width, height = resolution
        return f"{width}x{height}"

    def render_start_page(self):
        screen = self.create_screen()

        menu_bar = tk.Frame(screen)
        menu_bar.pack(side=tk.TOP, fill=tk.X)

        buttons = (
            ("Сюжетная игра", self.main_story_game),
            (
                "Бесконечная игра",
                self.infinity_game,
            ),  # оставить уведу о том что будет реализовано в будущем
            ("Настройки", self.open_settings),
            ("Выход", self.close_game),
        )

        self.create_button_row(menu_bar, buttons)

        empty_background = tk.Frame(screen)
        empty_background.pack(fill=tk.BOTH, expand=True)

    def open_settings(self):
        screen = self.create_screen()

        settings_area = tk.Frame(screen)
        settings_area.pack(fill=tk.BOTH, expand=True)

        current_window_mode = WINDOW_MODES[1] if self.is_fullscreen else WINDOW_MODES[0]
        self.selected_window_mode = tk.StringVar(value=current_window_mode)
        self.create_option_row(
            settings_area,
            "Режим окна:",
            self.selected_window_mode,
            WINDOW_MODES,
            command=self.update_resolution_state,
        )

        self.selected_resolution = tk.StringVar(value=self.current_resolution)
        resolution_options = [
            self.format_resolution(resolution) for resolution in AVAILABLE_RESOLUTIONS
        ]
        _, self.resolution_menu = self.create_option_row(
            settings_area,
            "Разрешение:",
            self.selected_resolution,
            resolution_options,
        )
        self.update_resolution_state()

        actions_bar = tk.Frame(screen)
        actions_bar.pack(side=tk.BOTTOM, fill=tk.X)
        self.create_button_row(
            actions_bar,
            (
                ("Назад", self.render_start_page),
                ("Подтвердить", self.apply_settings),
            ),
        )

    def apply_settings(self):
        self.is_fullscreen = self.selected_window_mode.get() == WINDOW_MODES[1]
        self.attributes("-fullscreen", self.is_fullscreen)

        selected_resolution = self.selected_resolution.get()
        for resolution in AVAILABLE_RESOLUTIONS:
            if selected_resolution == self.format_resolution(resolution):
                self.current_resolution = selected_resolution
                if not self.is_fullscreen:
                    self.geometry(selected_resolution)
                break

        self.update_idletasks()

    def update_resolution_state(self, *_):
        if self.selected_window_mode.get() == WINDOW_MODES[1]:
            self.resolution_menu.configure(state=tk.DISABLED)
        else:
            self.resolution_menu.configure(state=tk.NORMAL)

    def main_story_game(self):
        pass

    def infinity_game(self):
        pass

    def close_game(self):
        self.destroy()


if __name__ == "__main__":
    MainMenu().mainloop()
