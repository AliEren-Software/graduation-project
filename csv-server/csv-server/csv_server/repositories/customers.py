from ..db import get_connection
from ..utils import serialize_db_value


def fetch_raw_customers_with_invalid_id():
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT
                    customer_id,
                    first_name,
                    last_name,
                    age,
                    gender,
                    occupation,
                    city,
                    region,
                    income_level,
                    marital_status,
                    education_level,
                    registration_date,
                    has_loyalty_program,
                    num_loyalty_points,
                    churn_flag
                FROM raw_.raw_customer
                WHERE customer_id <= 0 OR customer_id IS NULL
            """)

            columns = [col[0].lower() for col in cursor.description]
            rows = cursor.fetchall()

            return [
                {
                    columns[index]: serialize_db_value(value)
                    for index, value in enumerate(row)
                }
                for row in rows
            ]


def fetch_customer_quality_counts():
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute("""
                WITH PRC_METRICS AS (
                    SELECT
                        COUNT(*) AS TOTAL_RECORD_COUNT,
                        (
                            SUM(CASE WHEN FIRST_NAME IN ('*', '?', '!') THEN 1 ELSE 0 END) +
                            SUM(CASE WHEN LAST_NAME IN ('*', '?', '!') THEN 1 ELSE 0 END) +
                            SUM(CASE WHEN AGE < -1 OR AGE IS NULL THEN 1 ELSE 0 END) +
                            SUM(CASE WHEN GENDER IN ('*', '?', '!','Unknown') THEN 1 ELSE 0 END) +
                            SUM(CASE WHEN OCCUPATION IN ('*', '?', '!') THEN 1 ELSE 0 END) +
                            SUM(CASE WHEN CITY IN ('*', '?', '!') THEN 1 ELSE 0 END) +
                            SUM(CASE WHEN REGION IN ('*', '?', '!') THEN 1 ELSE 0 END) +
                            SUM(CASE WHEN INCOME_LEVEL IN ('*', '?', '!') THEN 1 ELSE 0 END) +
                            SUM(CASE WHEN MARITAL_STATUS IN ('*', '?', '!','Unknown') THEN 1 ELSE 0 END) +
                            SUM(CASE WHEN EDUCATION_LEVEL IN ('*', '?', '!') THEN 1 ELSE 0 END) +
                            SUM(CASE WHEN REGISTRATION_DATE IS NULL THEN 1 ELSE 0 END) +
                            SUM(CASE WHEN HAS_LOYALTY_PROGRAM < -1 THEN 1 ELSE 0 END) +
                            SUM(CASE WHEN NUM_LOYALTY_POINTS < -1 THEN 1 ELSE 0 END) +
                            SUM(CASE WHEN CHURN_FLAG < -1 THEN 1 ELSE 0 END)
                        ) AS TOTAL_NULL_CELLS
                    FROM PRC_.prc_customer
                ),
                RAW_METRICS AS (
                    SELECT
                        COUNT(*) AS TOTAL_RECORD_COUNT,
                        (
                            SUM(CASE WHEN FIRST_NAME IN ('*', '?', '!') THEN 1 ELSE 0 END) +
                            SUM(CASE WHEN LAST_NAME IN ('*', '?', '!') THEN 1 ELSE 0 END) +
                            SUM(CASE WHEN AGE < 0 OR AGE IS NULL THEN 1 ELSE 0 END) +
                            SUM(CASE WHEN GENDER IN ('*', '?', '!','Unknown') THEN 1 ELSE 0 END) +
                            SUM(CASE WHEN OCCUPATION IN ('*', '?', '!') THEN 1 ELSE 0 END) +
                            SUM(CASE WHEN CITY IN ('*', '?', '!') THEN 1 ELSE 0 END) +
                            SUM(CASE WHEN REGION IN ('*', '?', '!') THEN 1 ELSE 0 END) +
                            SUM(CASE WHEN INCOME_LEVEL IN ('*', '?', '!') THEN 1 ELSE 0 END) +
                            SUM(CASE WHEN MARITAL_STATUS IN ('*', '?', '!','Unknown') THEN 1 ELSE 0 END) +
                            SUM(CASE WHEN EDUCATION_LEVEL IN ('*', '?', '!') THEN 1 ELSE 0 END) +
                            SUM(CASE WHEN REGISTRATION_DATE IS NULL THEN 1 ELSE 0 END) +
                            SUM(CASE WHEN HAS_LOYALTY_PROGRAM IS NULL OR HAS_LOYALTY_PROGRAM < 0 THEN 1 ELSE 0 END) +
                            SUM(CASE WHEN NUM_LOYALTY_POINTS < 0 OR NUM_LOYALTY_POINTS IS NULL THEN 1 ELSE 0 END) +
                            SUM(CASE WHEN CHURN_FLAG < -1 OR CHURN_FLAG IS NULL THEN 1 ELSE 0 END)
                        ) AS TOTAL_NULL_CELLS
                    FROM raw_.raw_customer
                )
                SELECT
                    P.TOTAL_RECORD_COUNT AS PROCESSED_RECORD_COUNT,
                    P.TOTAL_NULL_CELLS AS PROCESSED_TOTAL_NULLS,
                    R.TOTAL_RECORD_COUNT AS RAW_RECORD_COUNT,
                    R.TOTAL_NULL_CELLS AS RAW_TOTAL_NULLS,
                    ABS(R.TOTAL_NULL_CELLS - P.TOTAL_NULL_CELLS) AS DATA_CLEANSED_COUNT
                FROM PRC_METRICS P, RAW_METRICS R
            """)

            row = cursor.fetchone()
            if not row:
                return None

            total_prc_record_count, prc_total_null, raw_record_count, raw_total_null, modified = row
            return {
                "TOTAL_PRC_RECORD_COUNT": serialize_db_value(total_prc_record_count),
                "PRC_TOTAL_NULL": serialize_db_value(prc_total_null),
                "RAW_RECORD_COUNT": serialize_db_value(raw_record_count),
                "RAW_TOTAL_NULL": serialize_db_value(raw_total_null),
                "MODIFIED": serialize_db_value(modified),
            }


def fetch_raw_customer_duplicate_count():
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT COUNT(*) - COUNT(DISTINCT CUSTOMER_ID) AS DUPLICATE_CUSTOMER_COUNT
                FROM raw_.raw_customer
            """)

            row = cursor.fetchone()
            if not row:
                return None

            return {
                "DUPLICATE_CUSTOMER_COUNT": serialize_db_value(row[0])
            }
