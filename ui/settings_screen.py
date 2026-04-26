import tkinter as tk
from tkinter import messagebox

from config import AVAILABLE_RESOLUTIONS
from ui.widgets import create_button_row, create_option_row

WINDOW_MODES = ("Оконный", "Полный экран")


class SettingsScreen(tk.Frame):
    def __init__(
        self,
        parent,
        is_fullscreen,
        current_resolution,
        format_resolution,
        on_back,
        on_apply,
    ):
        super().__init__(parent)
        self.format_resolution = format_resolution
        self.on_back = on_back
        self.on_apply = on_apply
        self.root = self.winfo_toplevel()

        self.selected_window_mode = tk.StringVar(
            value=WINDOW_MODES[1] if is_fullscreen else WINDOW_MODES[0]
        )
        self.selected_resolution = tk.StringVar(value=current_resolution)
        self.saved_window_mode = self.selected_window_mode.get()
        self.saved_resolution = self.selected_resolution.get()

        settings_area = tk.Frame(self)
        settings_area.pack(fill=tk.BOTH, expand=True)

        create_option_row(
            settings_area,
            "Режим окна:",
            self.selected_window_mode,
            WINDOW_MODES,
            command=self.update_resolution_state,
        )

        resolution_options = [
            self.format_resolution(resolution) for resolution in AVAILABLE_RESOLUTIONS
        ]
        _, self.resolution_menu = create_option_row(
            settings_area,
            "Разрешение:",
            self.selected_resolution,
            resolution_options,
        )
        self.update_resolution_state()

        actions_bar = tk.Frame(self)
        actions_bar.pack(side=tk.BOTTOM, fill=tk.X)
        create_button_row(
            actions_bar,
            (
                ("Назад", self.close),
                ("Подтвердить", self.apply),
            ),
        )
        self.root.bind("<Escape>", self.close)

    def apply(self):
        is_fullscreen = self.selected_window_mode.get() == WINDOW_MODES[1]
        self.on_apply(is_fullscreen, self.selected_resolution.get())
        self.saved_window_mode = self.selected_window_mode.get()
        self.saved_resolution = self.selected_resolution.get()

    def close(self, *_):
        if self.has_unsaved_changes() and not messagebox.askyesno(
            "Настройки не сохранены",
            "Вы уверены, что хотите выйти без сохранения настроек?",
            parent=self,
        ):
            return

        self.root.unbind("<Escape>")
        self.on_back()

    def has_unsaved_changes(self):
        return (
            self.selected_window_mode.get() != self.saved_window_mode
            or self.selected_resolution.get() != self.saved_resolution
        )

    def update_resolution_state(self, *_):
        if self.selected_window_mode.get() == WINDOW_MODES[1]:
            self.resolution_menu.configure(state=tk.DISABLED)
        else:
            self.resolution_menu.configure(state=tk.NORMAL)
