"""Configuration and event-routing contracts for the monitor."""

import os
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from general_functions.config import load_local_env, load_settings, validate_paths
from general_functions.database import get_connection
from general_functions.handlers import MainHandler
from general_functions.runner import wait_until_file_ready


class MonitorTests(unittest.TestCase):
    def setUp(self):
        self.root = Path(__file__).parent / "nonexistent-monitor-root"
        self.env = {
            "RAW_FILES_ROOT": str(self.root),
            "ORACLE_HOST": "localhost",
            "ORACLE_PORT": "1521",
            "ORACLE_SERVICE_NAME": "testdb",
            "ORACLE_USER": "MONITOR_APP",
            "ORACLE_PASSWORD": "test-only-password",
        }

    def settings(self):
        with patch.dict(os.environ, self.env):
            return load_settings()

    def test_dataset_paths_are_derived_from_configured_root(self):
        settings = self.settings()
        self.assertEqual(len(settings.datasets), 12)
        customer = settings.datasets[0]
        region = settings.datasets[1]
        self.assertEqual(customer.watch_directory, self.root / "Customer" / "Insert_Out")
        self.assertEqual(customer.filename, "raw_customer_dataset.csv")
        self.assertEqual(
            region.processor,
            self.root / "Region" / "py_files" / "region_folder_monitor" / "monitor.py",
        )

    def test_process_environment_overrides_local_env(self):
        with patch.dict(os.environ, {"ORACLE_HOST": "process-host"}, clear=True):
            with patch.object(Path, "is_file", return_value=True):
                with patch.object(Path, "read_text", return_value="ORACLE_HOST=file-host\nEXTRA=value\n"):
                    load_local_env(Path("sample.env"))
            self.assertEqual(os.environ["ORACLE_HOST"], "process-host")
            self.assertEqual(os.environ["EXTRA"], "value")

    def test_rejects_privileged_oracle_account(self):
        with patch.dict(os.environ, {**self.env, "ORACLE_USER": "SYS"}):
            with self.assertRaisesRegex(ValueError, "dedicated application account"):
                load_settings()

    def test_connection_uses_regular_account(self):
        with patch("oracledb.makedsn", return_value="test-dsn"):
            with patch("oracledb.connect") as connect:
                get_connection(self.settings())
        self.assertEqual(connect.call_args.kwargs["user"], "MONITOR_APP")
        self.assertNotIn("mode", connect.call_args.kwargs)

    def test_missing_external_paths_are_reported(self):
        with self.assertRaisesRegex(FileNotFoundError, "Missing monitor paths"):
            validate_paths(self.settings())

    def test_main_handler_routes_only_matching_dataset_file(self):
        with patch("general_functions.handlers.ScriptRunner") as runner_factory:
            handler = MainHandler(self.settings())
            matching = SimpleNamespace(
                is_directory=False,
                src_path=str(self.root / "Customer" / "raw_customer_dataset.csv"),
            )
            unrelated = SimpleNamespace(
                is_directory=False,
                src_path=str(self.root / "Customer" / "notes.txt"),
            )
            handler.on_created(unrelated)
            handler.on_created(matching)
            handler.on_modified(matching)
        runner_factory.return_value.trigger.assert_called_once_with(matching.src_path)

    def test_unready_file_times_out(self):
        with self.assertRaises(TimeoutError):
            wait_until_file_ready(str(self.root / "missing.csv"), checks=2, delay=0)


if __name__ == "__main__":
    unittest.main()
