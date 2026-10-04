# CSV Server

Flask API for CSV uploads, ODI session status and customer quality reports stored in Oracle.

## Architecture

```text
server.py                    # application entry point
csv_server/__init__.py       # Flask application factory
csv_server/config.py         # environment settings and validation
csv_server/db.py             # Oracle connection boundary
csv_server/routes/api.py     # HTTP routes and authorization
csv_server/services/         # upload workflow
csv_server/repositories/     # database queries
.env.example                 # configuration template
```

For the component diagram and data paths, see the [architecture notes](../architecture/README.md).

## Setup

Requires Python 3.10+, an Oracle database and an application account with the grants in [docs/oracle-privileges.sql](docs/oracle-privileges.sql). Create that account with a **new random password**. Do not connect as `SYS` or `SYSTEM`.

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
if (-not (Test-Path .env)) { Copy-Item .env.example .env }
```

Fill in `.env` with `UPLOAD_TOKEN`, `ORACLE_HOST`, `ORACLE_PORT`, `ORACLE_SID`, `ORACLE_USER` and `ORACLE_PASSWORD`. All six are required. Generate a unique token locally, for example:

```powershell
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

Never commit `.env` or put real credentials in examples. Environment variables supplied by the process take precedence over `.env`. The server refuses to start when a required setting is missing or when `ORACLE_USER` is `SYS` or `SYSTEM`.

`UPLOAD_FOLDER` and `DUPLICATE_FOLDER` are optional local paths. Set `RAW_FILES_ROOT` to the parent folder of the `Customer`, `Region`, and other ODI input folders to route known dataset filenames there. If it is empty, all uploads use `UPLOAD_FOLDER`. The maximum request size is 5 MiB.

```powershell
python server.py
```

The default address is `http://localhost:5000`.

## Authentication

Every API endpoint requires an `Authorization` header. Query string tokens are ignored.

```bash
curl -H "Authorization: Bearer <UPLOAD_TOKEN>" "http://localhost:5000/file-status"
curl -X POST -H "Authorization: Bearer <UPLOAD_TOKEN>" -F "file=@example.csv" "http://localhost:5000/upload"
```

Use HTTPS when accessing the API over a network. See [ENDPOINTS.md](ENDPOINTS.md) and [customer_endpoints.md](customer_endpoints.md) for response details.
