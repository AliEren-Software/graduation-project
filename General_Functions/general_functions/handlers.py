"""Filesystem events for processor and cloud workflows."""

import logging
import os
import time

from watchdog.events import FileSystemEventHandler

from .config import Settings
from .database import mark_latest_cloud_status_only_success, update_latest_odi_cleaning_status
from .runner import ScriptRunner, write_error_log


logger = logging.getLogger("MonitorApp")


class DebouncedHandler(FileSystemEventHandler):
    def __init__(self):
        super().__init__()
        self.last_events = {}

    def on_created(self, event):
        self.handle_event(event)

    def on_modified(self, event):
        self.handle_event(event)

    def on_moved(self, event):
        self.handle_event(event, getattr(event, "dest_path", None))

    def should_process(self, file_path):
        now = time.monotonic()
        last_time = self.last_events.get(file_path)
        self.last_events[file_path] = now
        if len(self.last_events) > 1024:
            self.last_events = {
                path: seen_at for path, seen_at in self.last_events.items()
                if now - seen_at <= 1.0
            }
        return last_time is None or now - last_time > 1.0


class MainHandler(DebouncedHandler):
    def __init__(self, settings: Settings):
        super().__init__()
        self.runners = {
            (dataset.name, dataset.filename): ScriptRunner(
                dataset.processor, f"[MAIN][{dataset.name}]"
            )
            for dataset in settings.datasets
        }

    def handle_event(self, event, path=None):
        if event.is_directory:
            return
        file_path = path or event.src_path
        key = (os.path.basename(os.path.dirname(file_path)), os.path.basename(file_path))
        runner = self.runners.get(key)
        if runner is None or not self.should_process(file_path):
            return
        logger.info("[MAIN] File: %s | Folder: %s", key[1], key[0])
        runner.trigger(file_path)


class CloudHandler(DebouncedHandler):
    def __init__(self, settings: Settings, dataset):
        super().__init__()
        self.label = dataset.name
        self.settings = settings
        self.runner = ScriptRunner(
            dataset.cloud_script,
            f"[CLOUD][{dataset.name}]",
            on_before_run=self._update_odi_cleaning_before_cloud,
            on_success=self._mark_cloud_success,
        )

    def handle_event(self, event, path=None):
        if event.is_directory:
            return
        file_path = path or event.src_path
        if os.path.basename(file_path).lower() == "error_log.txt":
            return
        if not self.should_process(file_path):
            return
        logger.info("[CLOUD][%s] New file: %s", self.label, file_path)
        self.runner.trigger(file_path)

    def _update_odi_cleaning_before_cloud(self, file_path):
        try:
            session_id, status = update_latest_odi_cleaning_status(self.settings)
            logger.info(
                "[CLOUD][%s] Oracle pre-update SUCCESS: session_id=%s ODI_CLEANING=%s",
                self.label, session_id, status,
            )
        except Exception as error:
            write_error_log(file_path, f"Oracle pre-update error: {error}")
            logger.exception("[CLOUD][%s] Oracle pre-update ERROR", self.label)
            raise

    def _mark_cloud_success(self, file_path):
        try:
            session_id = mark_latest_cloud_status_only_success(self.settings)
            logger.info(
                "[CLOUD][%s] Oracle update SUCCESS: session_id=%s cloud_status=success",
                self.label, session_id,
            )
        except Exception as error:
            write_error_log(file_path, f"Oracle update error: {error}")
            logger.exception("[CLOUD][%s] Oracle update ERROR", self.label)
