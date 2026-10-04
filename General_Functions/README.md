# General Functions

A Windows file monitor for ODI automation. It watches CSV files in datasets under `RAW_FILES_ROOT`, runs the matching processor script, runs a cloud transfer script when files appear in `Insert_Out`, and updates the latest ODI session status in Oracle.

See the [architecture diagram and component notes](architecture/README.md) for the runtime paths and external boundaries.

## Structure

```text
General_Folder_Monitor.py       Entry point
general_functions/config.py     .env settings, datasets, and paths
general_functions/handlers.py   Main and cloud file events
general_functions/runner.py     Script queue, duplicate events, and error logs
general_functions/database.py   Oracle queries and connection
general_functions/gui.py        Tkinter window and observers
docs/oracle-privileges.sql      Required application account privileges
.env.example                    Shareable configuration template
.env                            Local settings (excluded from Git)
```

## Setup

Requires Python 3.10+, Tkinter, Oracle access, and the external ODI folders to monitor. Run these commands in this directory with PowerShell:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
if (-not (Test-Path .env)) { Copy-Item .env.example .env }
```

The included `.env` is a starting file with blank credentials. Fill in `ORACLE_USER` and `ORACLE_PASSWORD`. `SYS` and `SYSTEM` accounts are rejected; use a dedicated account with the [required Oracle privileges](docs/oracle-privileges.sql). An earlier version had a hardcoded password. Rotate it in Oracle if it was used. Keep `.env` private and out of Git.

`RAW_FILES_ROOT` is the parent folder. Change the example path `C:\data\watch\input\Raw_Files` to match your installation. `ORACLE_HOST`, `ORACLE_PORT`, and `ORACLE_SERVICE_NAME` configure the Oracle connection. Process environment variables take precedence over `.env` values.

Supported datasets: `Customer`, `Region`, `Subscription`, `Subscription_Packages`, `Package`, `Offers`, `Campaign_Memberships`, `Campaign_Responses`, `Customer_Offers`, `Billing`, `Support`, and `Usage`.

Default paths for each dataset:

- Watch directory: `<RAW_FILES_ROOT>/<DATASET>/Insert_Out`
- Processor: `<RAW_FILES_ROOT>/<DATASET>/py_files/customer_folder_monitor/monitor.py`; `Region` uses `region_folder_monitor`.
- Cloud script: `<RAW_FILES_ROOT>/<DATASET>/py_files/py_to_Cloud/to_Cloud.py`

For a different layout, set `<DATASET>_WATCH_DIRECTORY`, `<DATASET>_PROCESSOR`, and `<DATASET>_CLOUD_SCRIPT` in `.env`, using the dataset name in uppercase. See `.env.example` for examples. The application checks that all required folders and scripts exist before starting.

## Run

```powershell
python General_Folder_Monitor.py
```

The main observer runs the matching processor when it sees `raw_<dataset>_dataset.csv` in a dataset folder. On a file event in `Insert_Out`, the cloud observer queries the ODI status, runs the cloud script, and updates `cloud_status` after success. Jobs for the same dataset are queued. Errors are written to `error_log.txt` beside the affected file.

The monitored folders and processor scripts are external to this project. Local tests cannot verify the live Oracle connection or file transfer without those resources.

## Test

```powershell
python -m unittest discover -s tests -v
```
