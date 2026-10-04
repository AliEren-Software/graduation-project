"""Runtime settings. Secrets come from the process environment or local .env."""

import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent


def load_local_env(path):
    """Load simple KEY=value entries without overriding deployment settings."""
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        name, separator, value = line.partition("=")
        if not separator:
            raise RuntimeError(f"Invalid setting in {path.name}")
        name = name.strip()
        if not name.isidentifier():
            raise RuntimeError(f"Invalid setting name in {path.name}")
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
            value = value[1:-1]
        os.environ.setdefault(name, value)


load_local_env(BASE_DIR / ".env")


def required_setting(name):
    value = os.getenv(name, "")
    stripped = value.strip()
    if not stripped or stripped.startswith("<"):
        raise RuntimeError(f"{name} must be configured in the environment")
    return value


UPLOAD_TOKEN = required_setting("UPLOAD_TOKEN")
ORACLE_HOST = required_setting("ORACLE_HOST")
ORACLE_SID = required_setting("ORACLE_SID")
ORACLE_USER = required_setting("ORACLE_USER")
ORACLE_PASSWORD = required_setting("ORACLE_PASSWORD")

if ORACLE_USER.strip().upper() in {"SYS", "SYSTEM"}:
    raise RuntimeError("ORACLE_USER must be a dedicated application account")

try:
    ORACLE_PORT = int(required_setting("ORACLE_PORT"))
except ValueError as error:
    raise RuntimeError("ORACLE_PORT must be an integer") from error
if not 1 <= ORACLE_PORT <= 65535:
    raise RuntimeError("ORACLE_PORT must be between 1 and 65535")

UPLOAD_FOLDER = os.getenv("UPLOAD_FOLDER", str(BASE_DIR / "uploads"))
DUPLICATE_FOLDER = os.getenv("DUPLICATE_FOLDER", str(BASE_DIR / "duplicate"))
RAW_FILES_ROOT = os.getenv("RAW_FILES_ROOT", "").strip()
ALLOWED_EXTENSIONS = {"csv", "txt"}
MAX_FILE_SIZE = 5 * 1024 * 1024

_DATASET_FOLDERS = {
    "raw_customer_dataset.csv": "Customer",
    "raw_region_dataset.csv": "Region",
    "raw_subscription_dataset.csv": "Subscription",
    "raw_package_dataset.csv": "Package",
    "raw_offers_dataset.csv": "Offers",
    "raw_campaign_memberships_dataset.csv": "Campaign_Memberships",
    "raw_customer_offers_dataset.csv": "Customer_Offers",
    "raw_billing_dataset.csv": "Billing",
    "raw_support_dataset.csv": "Support",
    "raw_usage_dataset.csv": "Usage",
    "raw_subscription_packages_dataset.csv": "Subscription_Packages",
    "raw_campaign_responses_dataset.csv": "Campaign_Responses",
}
FILE_DESTINATIONS = (
    {name: str(Path(RAW_FILES_ROOT) / folder) for name, folder in _DATASET_FOLDERS.items()}
    if RAW_FILES_ROOT else {}
)


def configure_app(app):
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    os.makedirs(DUPLICATE_FOLDER, exist_ok=True)
    app.config["MAX_CONTENT_LENGTH"] = MAX_FILE_SIZE
