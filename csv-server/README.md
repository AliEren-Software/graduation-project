# CSV Server

The Flask application for CSV uploads, ODI session status, and customer quality reports is in the nested [`csv-server/`](csv-server/) directory. Its code, settings, and tests stay together there.

See the [architecture diagram and component notes](architecture/README.md) for the API and storage paths.

## Getting started

```powershell
Set-Location .\csv-server
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

Follow the Oracle account and API token setup in the inner [README](csv-server/README.md). The configuration template is [`csv-server/.env.example`](csv-server/.env.example). Local settings belong in `csv-server/.env`, which is excluded from Git.

```powershell
python server.py
python -m unittest discover -s tests -v
```

See [ENDPOINTS.md](csv-server/ENDPOINTS.md) and [customer_endpoints.md](csv-server/customer_endpoints.md) for API routes. This API may use the same Oracle database and raw data directories as `General_Functions`; each application has its own settings and dependencies.
