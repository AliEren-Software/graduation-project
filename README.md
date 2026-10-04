# Graduation Project

This repository contains two independent Python applications for a CSV and ODI processing workflow. Each application keeps its code, settings, documentation, and tests in its own directory.

| Application | Purpose | Setup | Architecture |
| --- | --- | --- | --- |
| [CSV Server](csv-server/README.md) | Flask API for CSV uploads, ODI session status, and customer quality reports | [Application README](csv-server/csv-server/README.md) | [Diagram and notes](csv-server/architecture/README.md) |
| [General Functions](General_Functions/README.md) | File monitoring, processor execution, and Oracle status updates | [Application README](General_Functions/README.md) | [Diagram and notes](General_Functions/architecture/README.md) |

The applications may use the same Oracle database and raw data directory, but they run separately and have their own dependencies and `.env` settings. Copy each `.env.example` into that application's `.env` file and fill in private values locally. Do not commit `.env` files.

## Run tests

Install each application's requirements, then run its tests from its own application directory:

```powershell
Set-Location .\csv-server\csv-server
python -m unittest discover -s tests -v

Set-Location ..\..\General_Functions
python -m unittest discover -s tests -v
```

The integration workflows require external ODI folders and Oracle access. The local unit tests do not connect to those services.
