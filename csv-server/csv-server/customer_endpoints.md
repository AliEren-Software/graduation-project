# Customer Endpoints

Base URL (use HTTPS and replace the host placeholder):

All requests require `Authorization: Bearer <UPLOAD_TOKEN>`.

```text
https://<API_HOST>
```

## `GET /customers/invalid-ids`

Lists records in `raw_.raw_customer` where `customer_id <= 0` or `customer_id IS NULL`.

Example:

```bash
curl -H "Authorization: Bearer <UPLOAD_TOKEN>" "https://<API_HOST>/customers/invalid-ids"
```

Successful response format:

```json
{
  "status": "success",
  "count": 2,
  "data": [
    {
      "customer_id": null,
      "first_name": "John",
      "last_name": "Doe",
      "age": 30,
      "gender": "M",
      "occupation": "Engineer",
      "city": "Istanbul",
      "region": "Marmara",
      "income_level": "High",
      "marital_status": "Single",
      "education_level": "Bachelor",
      "registration_date": "2024-01-15T00:00:00",
      "has_loyalty_program": 1,
      "num_loyalty_points": 100,
      "churn_flag": 0
    }
  ]
}
```

Each record in `data` includes these fields:

- `customer_id`
- `first_name`
- `last_name`
- `age`
- `gender`
- `occupation`
- `city`
- `region`
- `income_level`
- `marital_status`
- `education_level`
- `registration_date`
- `has_loyalty_program`
- `num_loyalty_points`
- `churn_flag`

Error response:

```json
{
  "status": "failed",
  "error_message": "..."
}
```

## `GET /customers/quality/null-counts`

Compares null and invalid value counts for selected fields in `raw_.raw_customer` and `PRC_.prc_customer`.

Alias:

- `GET /customer-quality-counts`

Example:

```bash
curl -H "Authorization: Bearer <UPLOAD_TOKEN>" "https://<API_HOST>/customers/quality/null-counts"
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

Fields in `data`:

- `TOTAL_PRC_RECORD_COUNT`: total records in `PRC_.prc_customer`
- `PRC_TOTAL_NULL`: total null or invalid cells in the processed table
- `RAW_RECORD_COUNT`: total records in `raw_.raw_customer`
- `RAW_TOTAL_NULL`: total null or invalid cells in the raw table
- `MODIFIED`: difference between raw and processed counts

If no data is found:

```json
{
  "error": "No data found"
}
```

Error response:

```json
{
  "status": "failed",
  "error_message": "..."
}
```

## `GET /raw/customers/duplicate-count`

Returns the number of duplicate `CUSTOMER_ID` values in `raw_.raw_customer`.

Alias:

- `GET /customers/duplicate-count`

Example:

```bash
curl -H "Authorization: Bearer <UPLOAD_TOKEN>" "https://<API_HOST>/raw/customers/duplicate-count"
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

If no data is found:

```json
{
  "error": "No data found"
}
```

Error response:

```json
{
  "status": "failed",
  "error_message": "..."
}
```
