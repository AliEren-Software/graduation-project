# API Endpoints

Base URL:

```text
http://localhost:5000
```

## `POST /upload`

Uploads a file. The `Authorization: Bearer <UPLOAD_TOKEN>` header is required. The same header protects every endpoint.

Example request:

```http
POST /upload
Authorization: Bearer <UPLOAD_TOKEN>
Content-Type: multipart/form-data
```

Form field:

- `file`: file to upload

Example `curl` command:

```bash
curl -X POST -H "Authorization: Bearer <UPLOAD_TOKEN>" -F "file=@example.csv" "http://localhost:5000/upload"
```

Successful response:

```json
{
  "status": "success",
  "job_id": 62,
  "filename": "example.csv",
  "path": "uploads\\example.csv"
}
```

Possible errors:

- `401 Unauthorized`: invalid token
- `400 Bad Request`: missing `file` field, empty filename, or unsupported extension
- `500 Internal Server Error`: could not retrieve `job_id` from Oracle

## `GET /odi/sessions/<sess_no>/status`

Returns the status of a specific ODI session.

Alias:

- `GET /odi-status/<sess_no>`

Example:

```bash
curl -H "Authorization: Bearer <UPLOAD_TOKEN>" "http://localhost:5000/odi/sessions/12345/status"
```

Successful response:

```json
{
  "job_id": 12345,
  "job_status": "success"
}
```

Failed session response:

```json
{
  "job_id": 12345,
  "job_status": "failed",
  "error_message": "ORA-..."
}
```

While processing:

```json
{
  "job_id": 12345,
  "job_status": "processing"
}
```

If the session is not found:

```json
{
  "error": "Session not found"
}
```

## `GET /customers/invalid-ids`

Lists records in `raw_.raw_customer` where `customer_id <= 0` or `customer_id IS NULL`.

Example:

```bash
curl -H "Authorization: Bearer <UPLOAD_TOKEN>" "http://localhost:5000/customers/invalid-ids"
```

Successful response format:

```json
{
  "status": "success",
  "count": 2,
  "data": [
    {
      "customer_id": null,
      "first_name": "John"
    }
  ]
}
```

## `GET /customers/quality/null-counts`

Compares aggregate null and invalid value counts for selected fields in `raw_.raw_customer` and `PRC_.prc_customer`.

Alias:

- `GET /customer-quality-counts`

Example:

```bash
curl -H "Authorization: Bearer <UPLOAD_TOKEN>" "http://localhost:5000/customers/quality/null-counts"
```

Successful response:

```json
{
  "status": "success",
  "data": {
    "TOTAL_PRC_RECORD_COUNT": 100,
    "PRC_TOTAL_NULL": 3,
    "RAW_RECORD_COUNT": 100,
    "RAW_TOTAL_NULL": 5,
    "MODIFIED": 2
  }
}
```

## `GET /raw/customers/duplicate-count`

Returns the number of duplicate `CUSTOMER_ID` values in `raw_.raw_customer`.

Alias:

- `GET /customers/duplicate-count`

Example:

```bash
curl -H "Authorization: Bearer <UPLOAD_TOKEN>" "http://localhost:5000/raw/customers/duplicate-count"
```

Successful response:

```json
{
  "status": "success",
  "data": {
    "DUPLICATE_CUSTOMER_COUNT": 0
  }
}
```

## `GET /file-status`

Returns all records from `PRC_.job_stats`, ordered by `session_id DESC`.

Example:

```bash
curl -H "Authorization: Bearer <UPLOAD_TOKEN>" "http://localhost:5000/file-status"
```

Successful response format:

```json
{
  "count": 2,
  "data": [
    {
      "session_id": 101,
      "cloud_status": null,
      "odi_cleaning": null
    }
  ]
}
```

## `GET /file-status/<session_id>`

Returns the record in `PRC_.job_stats` for the given `session_id`.

Example:

```bash
curl -H "Authorization: Bearer <UPLOAD_TOKEN>" "http://localhost:5000/file-status/101"
```

Successful response format:

```json
{
  "data": {
    "session_id": 101,
    "cloud_status": null,
    "odi_cleaning": null
  }
}
```

If the record is not found:

```json
{
  "error": "Session not found"
}
```
