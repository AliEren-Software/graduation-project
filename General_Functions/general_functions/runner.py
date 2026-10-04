"""Queue processor scripts and suppress duplicate filesystem events."""

import logging
import os
import subprocess
import sys
import threading
import time
from collections import deque
from datetime import datetime
from pathlib import Path


logger = logging.getLogger("MonitorApp")


def write_error_log(file_path: str, error_message: str) -> None:
    log_file = Path(file_path).parent / "error_log.txt"
    with log_file.open("a", encoding="utf-8") as log:
        log.write(f"\n[{datetime.now()}]\n{error_message}\n")


def wait_until_file_ready(file_path: str, checks: int = 5, delay: float = 0.3) -> None:
    """Wait until a file has the same size in two consecutive checks."""
    last_size = None
    for _ in range(checks):
        try:
            size = os.path.getsize(file_path)
        except OSError:
            size = None
        if size is not None and size == last_size:
            return
        last_size = size
        time.sleep(delay)
    raise TimeoutError(f"File was not ready: {file_path}")


class ScriptRunner:
    RECENT_PROCESS_TTL_SECONDS = 60

    def __init__(self, script, label, on_before_run=None, on_success=None):
        self.script = str(script)
        self.label = label
        self.on_before_run = on_before_run
        self.on_success = on_success
        self.lock = threading.Lock()
        self.running = False
        self.pending_files = deque()
        self.inflight_files = set()
        self.recently_processed = {}

    def trigger(self, file_path):
        if not self.script:
            logger.error("%s Script path is empty.", self.label)
            write_error_log(file_path, "Script path is empty.")
            return

        with self.lock:
            self._cleanup_recently_processed_locked()
            current_signature = self._get_file_signature(file_path)
            recent_entry = self.recently_processed.get(file_path)
            if recent_entry and recent_entry[0] == current_signature:
                logger.info("%s Recently processed duplicate ignored for %s.", self.label, os.path.basename(file_path))
                return
            if file_path in self.inflight_files:
                logger.info("%s Duplicate file event ignored for %s.", self.label, os.path.basename(file_path))
                return

            self.pending_files.append(file_path)
            self.inflight_files.add(file_path)
            if self.running:
                logger.info("%s Script is running; queued file event for %s.", self.label, os.path.basename(file_path))
                return
            self.running = True
            threading.Thread(target=self._run_loop, daemon=True).start()

    def _run_loop(self):
        while True:
            with self.lock:
                if not self.pending_files:
                    self.running = False
                    return
                file_path = self.pending_files.popleft()

            try:
                wait_until_file_ready(file_path)
                if self.on_before_run:
                    self.on_before_run(file_path)
                subprocess.run([sys.executable, self.script], check=True)
                logger.info("%s SUCCESS: %s", self.label, self.script)
                if self.on_success:
                    self.on_success(file_path)
            except Exception as error:
                try:
                    write_error_log(file_path, str(error))
                except OSError:
                    logger.exception("%s Could not write error_log.txt", self.label)
                logger.exception("%s ERROR: %s", self.label, error)
            finally:
                with self.lock:
                    self.recently_processed[file_path] = (self._get_file_signature(file_path), time.time())
                    self.inflight_files.discard(file_path)

    @staticmethod
    def _get_file_signature(file_path):
        try:
            stat = os.stat(file_path)
            return stat.st_size, stat.st_mtime_ns
        except OSError:
            return None

    def _cleanup_recently_processed_locked(self):
        cutoff = time.time() - self.RECENT_PROCESS_TTL_SECONDS
        stale_paths = [
            path for path, (_, processed_at) in self.recently_processed.items()
            if processed_at < cutoff
        ]
        for path in stale_paths:
            self.recently_processed.pop(path, None)
