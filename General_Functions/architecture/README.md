# General Functions architecture

Open the [interactive architecture diagram](architecture.html) to explore the components. Its editable Archify specification is [architecture.json](architecture.json). The diagram shows the current code and its external dependencies; it does not describe the internals of the ODI scripts.

## Components and code

| Component | Responsibility | Source |
| --- | --- | --- |
| Entry point and settings | Load `.env`, build dataset paths, reject privileged Oracle accounts, and start the GUI | [`General_Folder_Monitor.py`](../General_Folder_Monitor.py), [`config.py`](../general_functions/config.py) |
| Tkinter UI and Watchdog | Display logs; start one recursive observer for `RAW_FILES_ROOT` and one nonrecursive observer per `Insert_Out` directory; stop observers on window close | [`gui.py`](../general_functions/gui.py) |
| Event handlers | Match raw dataset filenames to processors; handle cloud folder events and Oracle status callbacks | [`handlers.py`](../general_functions/handlers.py) |
| Script runner | Queue work per script, suppress repeated events, wait for files to settle, run external Python scripts, and write errors beside the affected file | [`runner.py`](../general_functions/runner.py) |
| Oracle boundary | Read the latest `PRC_.job_stats` session and its ODI status; update `ODI_CLEANING`, `ODI_ERROR_MESAGE`, and `cloud_status` | [`database.py`](../general_functions/database.py) |
| External inputs | ODI dataset folders, processor scripts, cloud scripts, and Oracle database | Configured in [`.env.example`](../.env.example); not included in this repository |

## Runtime paths

1. **Raw dataset:** A file such as `Customer/raw_customer_dataset.csv` arrives under `RAW_FILES_ROOT`. The recursive observer passes the event to `MainHandler`, which selects the dataset processor. `ScriptRunner` waits for the file to stabilize and starts the script with the current Python interpreter.
2. **Cloud output:** A file appears in a dataset's `Insert_Out` directory. `CloudHandler` reads the latest ODI session and writes its cleaning status to Oracle before starting the cloud script. After the script succeeds, it marks that latest session's `cloud_status` as `success`.
3. **Shutdown:** Closing the Tkinter window stops and joins all observers.

`config.py` derives paths for twelve datasets from `RAW_FILES_ROOT`; each watch directory, processor, or cloud script can be overridden in `.env`. Process environment variables take precedence over `.env`. Database calls use a dedicated application account and bound SQL values. See [Oracle privileges](../docs/oracle-privileges.sql).

## Boundaries and limitations

The monitor runs as one local desktop process. The ODI scripts and Oracle service are external, so the unit tests cannot verify live execution. File event suppression and script queues are held in memory. The cloud status callback logs a database update failure after a successful script; that failure does not rerun the script automatically.

The CSV Server is a separate application. It can write into the same raw data folders when `RAW_FILES_ROOT` is configured consistently; see its [architecture notes](../../csv-server/architecture/README.md).
