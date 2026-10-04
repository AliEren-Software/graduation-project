"""Launch the General Functions folder monitor."""

import tkinter as tk

from general_functions.config import load_settings
from general_functions.gui import App


def main():
    settings = load_settings()
    root = tk.Tk()
    App(root, settings)
    root.mainloop()


if __name__ == "__main__":
    main()
