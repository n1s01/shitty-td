import tkinter as tk

from config import WINDOW_HEIGHT, WINDOW_WIDTH


class MainMenu(tk.Tk):
    def __init__(self) -> None:
        super().__init__()

        self.title("Tower Deffense")
        self.geometry(f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}")
        self.minsize(640, 360)
        self.protocol("WM_DELETE_WINDOW", self.close_game)

        self.create_menu()

    def create_menu(self) -> None:
        menu_bar = tk.Frame(self)
        menu_bar.pack(side=tk.TOP, fill=tk.X)

        buttons_frame = tk.Frame(menu_bar)
        buttons_frame.pack(side=tk.TOP)

        buttons = (
            ("Сюжетная игра", self.placeholder_action),
            ("Бесконечная игра", self.placeholder_action),
            ("Настройки", self.placeholder_action),
            ("Выход", self.close_game),
        )

        for text, command in buttons:
            button = tk.Button(buttons_frame, text=text, command=command)
            button.pack(side=tk.LEFT)

        empty_background = tk.Frame(self)
        empty_background.pack(fill=tk.BOTH, expand=True)

    def placeholder_action(self) -> None:
        pass

    def close_game(self) -> None:
        self.destroy()


if __name__ == "__main__":
    MainMenu().mainloop()
