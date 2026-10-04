# CSV Server architecture

Open the [interactive architecture diagram](architecture.html) to explore the components. Its editable Archify specification is [architecture.json](architecture.json). The application code is in the nested [`csv-server/`](../csv-server/) directory.

## Components and code

| Component | Responsibility | Source |
| --- | --- | --- |
| Entry point and application factory | Start Flask, configure the application, and register routes | [`server.py`](../csv-server/server.py), [`csv_server/__init__.py`](../csv-server/csv_server/__init__.py) |
| Configuration | Load `.env`, validate the upload token and Oracle account, and map known dataset filenames to raw folders | [`config.py`](../csv-server/csv_server/config.py) |
| API routes | Require a Bearer token for every endpoint; dispatch uploads and status or quality requests | [`routes/api.py`](../csv-server/csv_server/routes/api.py) |
| Upload service | Check file extension, sanitize filenames, keep concurrent duplicate uploads apart, save files, and reserve a job ID | [`services/upload_service.py`](../csv-server/csv_server/services/upload_service.py) |
| Repositories and Oracle boundary | Query ODI sessions and customer reports; insert and read `PRC_.job_stats` through a regular Oracle connection | [`repositories/`](../csv-server/csv_server/repositories/), [`db.py`](../csv-server/csv_server/db.py) |
| External storage | Save known dataset filenames under `RAW_FILES_ROOT` when configured; otherwise use `UPLOAD_FOLDER`. Duplicates go to `DUPLICATE_FOLDER` | Configured in [`.env.example`](../csv-server/.env.example) |

## Request paths

1. **Authentication:** The `before_request` hook checks `Authorization: Bearer <UPLOAD_TOKEN>` before any API handler runs. Query string tokens are ignored.
2. **Upload:** `POST /upload` passes a CSV or TXT file to the upload service. The service sanitizes its name, selects the target directory, and saves duplicates separately. For a primary upload it inserts a `job_stats` record to reserve a job ID, then returns the file path and job ID.
3. **Reads:** ODI status, file status, and customer quality routes call repositories. Repositories use bound SQL parameters where values are supplied by a request.

The request size limit is 5 MiB. `ORACLE_USER` must be a dedicated account; the code does not connect in SYSDBA mode. See [required Oracle privileges](../csv-server/docs/oracle-privileges.sql) and [endpoint details](../csv-server/ENDPOINTS.md).

## Boundaries and limitations

Oracle and the optional raw data directory are external. The in-memory active upload set coordinates duplicates only within one server process. The database handles job ID uniqueness through an insert and retry on a unique constraint error. Local tests cover authorization and the nonprivileged Oracle connection; they do not exercise a live Oracle database.

The General Functions monitor can process files written into the shared raw data folders when both applications are configured for the same location; see its [architecture notes](../../General_Functions/architecture/README.md).
