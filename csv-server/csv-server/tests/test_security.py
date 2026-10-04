"""Security contract for configuration, Oracle access and HTTP authorization."""

import os
import unittest
from unittest.mock import patch


_test_settings = {
    "UPLOAD_TOKEN": "test-token-with-at-least-thirty-two-characters",
    "ORACLE_HOST": "localhost",
    "ORACLE_PORT": "1521",
    "ORACLE_SID": "testdb",
    "ORACLE_USER": "CSV_SERVER_APP",
    "ORACLE_PASSWORD": "test-only-password",
}
os.environ.update(_test_settings)

from csv_server import create_app  # noqa: E402
from csv_server import db  # noqa: E402


class SecurityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with patch("csv_server.config.os.makedirs"):
            cls.client = create_app().test_client()

    def test_every_endpoint_requires_authorization(self):
        for path in ("/upload", "/file-status", "/customers/invalid-ids"):
            method = "post" if path == "/upload" else "get"
            with self.subTest(path=path):
                response = getattr(self.client, method)(path)
                self.assertEqual(response.status_code, 401)

    def test_query_token_does_not_authenticate(self):
        response = self.client.get("/file-status?token=" + _test_settings["UPLOAD_TOKEN"])
        self.assertEqual(response.status_code, 401)

    def test_bearer_header_authenticates(self):
        with patch("csv_server.routes.api.fetch_file_status_rows", return_value=[]):
            response = self.client.get(
                "/file-status",
                headers={"Authorization": "Bearer " + _test_settings["UPLOAD_TOKEN"]},
            )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json["count"], 0)

    def test_oracle_connection_has_no_privileged_mode(self):
        with patch("csv_server.db.oracledb.connect") as connect:
            db.get_connection()
        self.assertEqual(connect.call_args.kwargs["user"], "CSV_SERVER_APP")
        self.assertNotIn("mode", connect.call_args.kwargs)


if __name__ == "__main__":
    unittest.main()
