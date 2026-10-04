from datetime import date, datetime
from decimal import Decimal


def clean_error_message(error_message):
    if not error_message:
        return "Unknown error"

    error_message = error_message.replace("\\/", "\\")

    for marker in ("File not found", "ORA-", "ODI-"):
        if marker in error_message:
            start = error_message.find(marker)
            return error_message[start:start + 200]

    return error_message[:300]


def serialize_db_value(value):
    if isinstance(value, (datetime, date)):
        return value.isoformat()

    if isinstance(value, Decimal):
        return float(value)

    return value
