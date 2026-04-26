import tkinter as tk


def create_button_row(parent, buttons):
    buttons_frame = tk.Frame(parent)
    buttons_frame.pack()

    for text, command in buttons:
        button = tk.Button(buttons_frame, text=text, command=command)
        button.pack(side=tk.LEFT, padx=4, pady=4)

    return buttons_frame


def create_option_row(parent, label_text, variable, options, command=None):
    row = tk.Frame(parent)
    row.pack(pady=10)

    label = tk.Label(row, text=label_text)
    label.pack(side=tk.LEFT, padx=5)

    menu = tk.OptionMenu(row, variable, *options, command=command)
    menu.pack(side=tk.LEFT, padx=5)

    return row, menu
