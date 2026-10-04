"""Load monitor settings from the process environment and local .env file."""

import os
from dataclasses import dataclass
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent


def load_local_env(path: Path = BASE_DIR / ".env") -> None:
    """Read simple KEY=value lines; process environment takes precedence."""
    if not path.is_file():
        return

    for number, raw_line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        name, separator, value = line.partition("=")
        name = name.strip()
        if not separator or not name.isidentifier():
            raise ValueError(f"Invalid .env entry on line {number}")
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
            value = value[1:-1]
        os.environ.setdefault(name, value)


def required(name: str) -> str:
    value = os.environ.get(name, "").strip()
    if not value or value.startswith("<"):
        raise ValueError(f"Set {name} in General_Functions/.env or the environment")
    return value


def path_setting(name: str, default: Path) -> Path:
    value = os.environ.get(name, "").strip()
    path = Path(value) if value else default
    return path if path.is_absolute() else BASE_DIR / path


@dataclass(frozen=True)
class Dataset:
    name: str
    filename: str
    watch_directory: Path
    processor: Path
    cloud_script: Path


@dataclass(frozen=True)
class Settings:
    raw_files_root: Path
    oracle_host: str
    oracle_port: int
    oracle_service_name: str
    oracle_user: str
    oracle_password: str
    datasets: tuple[Dataset, ...]


DATASET_NAMES = (
    "Customer",
    "Region",
    "Subscription",
    "Subscription_Packages",
    "Package",
    "Offers",
    "Campaign_Memberships",
    "Campaign_Responses",
    "Customer_Offers",
    "Billing",
    "Support",
    "Usage",
)


def load_settings() -> Settings:
    load_local_env()
    raw_files_root = Path(required("RAW_FILES_ROOT"))
    if not raw_files_root.is_absolute():
        raw_files_root = BASE_DIR / raw_files_root
    oracle_user = required("ORACLE_USER")
    if oracle_user.upper() in {"SYS", "SYSTEM"}:
        raise ValueError("ORACLE_USER must be a dedicated application account")

    try:
        oracle_port = int(required("ORACLE_PORT"))
    except ValueError as error:
        raise ValueError("ORACLE_PORT must be an integer from 1 to 65535") from error
    if not 1 <= oracle_port <= 65535:
        raise ValueError("ORACLE_PORT must be an integer from 1 to 65535")

    datasets = []
    for name in DATASET_NAMES:
        key = name.upper()
        folder = raw_files_root / name
        processor_folder = "region_folder_monitor" if name == "Region" else "customer_folder_monitor"
        datasets.append(
            Dataset(
                name=name,
                filename=f"raw_{name.lower()}_dataset.csv",
                watch_directory=path_setting(f"{key}_WATCH_DIRECTORY", folder / "Insert_Out"),
                processor=path_setting(
                    f"{key}_PROCESSOR", folder / "py_files" / processor_folder / "monitor.py"
                ),
                cloud_script=path_setting(
                    f"{key}_CLOUD_SCRIPT", folder / "py_files" / "py_to_Cloud" / "to_Cloud.py"
                ),
            )
        )

    return Settings(
        raw_files_root=raw_files_root,
        oracle_host=required("ORACLE_HOST"),
        oracle_port=oracle_port,
        oracle_service_name=required("ORACLE_SERVICE_NAME"),
        oracle_user=oracle_user,
        oracle_password=required("ORACLE_PASSWORD"),
        datasets=tuple(datasets),
    )


def validate_paths(settings: Settings) -> None:
    """Report missing external ODI folders and scripts before starting observers."""
    missing = []
    if not settings.raw_files_root.is_dir():
        missing.append(str(settings.raw_files_root))
    for dataset in settings.datasets:
        if not dataset.watch_directory.is_dir():
            missing.append(str(dataset.watch_directory))
        for script in (dataset.processor, dataset.cloud_script):
            if not script.is_file():
                missing.append(str(script))
    if missing:
        raise FileNotFoundError("Missing monitor paths:\n" + "\n".join(missing))
