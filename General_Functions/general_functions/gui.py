"""Tkinter monitor window and watchdog observer lifecycle."""

import logging
import tkinter as tk
from tkinter.scrolledtext import ScrolledText

from watchdog.observers import Observer

from .config import Settings, validate_paths
from .handlers import CloudHandler, MainHandler


logger = logging.getLogger("MonitorApp")
logger.setLevel(logging.INFO)


class GuiLoggerHandler(logging.Handler):
    def __init__(self, widget):
        super().__init__()
        self.widget = widget

    def emit(self, record):
        message = self.format(record)
        self.widget.after(0, self._append, message)

    def _append(self, message):
        self.widget.insert(tk.END, message + "\n")
        self.widget.see(tk.END)


class App:
    def __init__(self, root: tk.Tk, settings: Settings):
        self.root = root
        self.root.title("Automation Monitor")
        self.text = ScrolledText(root, width=110, height=30)
        self.text.pack()
        self.log_handler = GuiLoggerHandler(self.text)
        self.log_handler.setFormatter(logging.Formatter("%(asctime)s - %(message)s"))
        logger.addHandler(self.log_handler)
        self.observers = []
        self.start_watchers(settings)
        self.root.protocol("WM_DELETE_WINDOW", self.stop)

    def start_watchers(self, settings: Settings):
        validate_paths(settings)
        main_observer = Observer()
        main_observer.schedule(MainHandler(settings), str(settings.raw_files_root), recursive=True)
        self.observers.append(main_observer)

        for dataset in settings.datasets:
            observer = Observer()
            observer.schedule(
                CloudHandler(settings, dataset), str(dataset.watch_directory), recursive=False
            )
            self.observers.append(observer)

        for observer in self.observers:
            observer.start()
        logger.info("System started. Watching MAIN: %s", settings.raw_files_root)
        for dataset in settings.datasets:
            logger.info("Watching CLOUD %s: %s", dataset.name, dataset.watch_directory)

    def stop(self):
        for observer in self.observers:
            observer.stop()
        for observer in self.observers:
            observer.join()
        logger.removeHandler(self.log_handler)
        self.root.destroy()
