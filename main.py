import tkinter as tk

from config import WINDOW_HEIGHT, WINDOW_WIDTH


class MainMenu(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title("Tower Deffense")
        self.geometry(f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}")
        self.minsize(640, 360)
        self.protocol("WM_DELETE_WINDOW", self.close_game)
        self.now_screen = None
        self.render_start_page()

    def clear(self):
        if self.now_screen is not None:
            self.now_screen.destroy()

    def render_start_page(self):
        self.clear()
        self.now_screen = tk.Frame(self)
        self.now_screen.pack(fill=tk.BOTH, expand=True)

        menu_bar = tk.Frame(self.now_screen)
        menu_bar.pack(side=tk.TOP, fill=tk.X)

        buttons_frame = tk.Frame(menu_bar)
        buttons_frame.pack(side=tk.TOP)

        buttons = (
            ("Сюжетная игра", self.main_story_game),
            (
                "Бесконечная игра",
                self.infinity_game,
            ),  # оставить уведу о том что будет реализовано в будущем
            ("Настройки", self.open_settings),
            ("Выход", self.close_game),
        )

        for text, command in buttons:
            button = tk.Button(buttons_frame, text=text, command=command)
            button.pack(side=tk.LEFT)

        empty_background = tk.Frame(self.now_screen)
        empty_background.pack(fill=tk.BOTH, expand=True)

    def open_settings(self):
        self.clear()

        self.now_screen = tk.Frame(self)
        self.now_screen.pack(fill=tk.BOTH, expand=True)

        menu_bar = tk.Frame(self.now_screen)
        menu_bar.pack(side=tk.TOP, fill=tk.X)

        buttons_frame = tk.Frame(menu_bar)
        buttons_frame.pack(side=tk.TOP)

        back_button = tk.Button(
            buttons_frame, text="Назад", command=self.render_start_page
        )
        back_button.pack(side=tk.LEFT)

        settings_area = tk.Frame(self.now_screen)
        settings_area.pack(fill=tk.BOTH, expand=True)

        title = tk.Label(settings_area, text="Настройки")
        title.pack()

    def main_story_game(self):
        pass

    def infinity_game(self):
        pass

    def close_game(self):
        self.destroy()


if __name__ == "__main__":
    MainMenu().mainloop()
