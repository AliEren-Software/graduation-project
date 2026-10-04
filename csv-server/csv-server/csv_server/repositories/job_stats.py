import threading

import oracledb

from ..db import get_connection
from ..utils import serialize_db_value


job_id_lock = threading.Lock()


def fetch_next_session_job_id():
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT COALESCE(MAX(SESS_NO), 0) + 2 AS NEXT_JOB_ID
                FROM DEV_ODI_REPO.SNP_SESSION
            """)

            row = cursor.fetchone()
            return int(row[0])


def is_unique_constraint_error(error):
    if not error.args:
        return False

    db_error = error.args[0]
    return getattr(db_error, "code", None) == 1


def insert_job_stats_record(session_id):
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute("""
                INSERT INTO PRC_.job_stats (
                    session_id,
                    cloud_status,
                    odi_cleaning
                ) VALUES (
                    :session_id,
                    :cloud_status,
                    :odi_cleaning
                )
            """, {
                "session_id": session_id,
                "cloud_status": None,
                "odi_cleaning": None,
            })

        conn.commit()


def reserve_job_id(max_attempts=10):
    with job_id_lock:
        last_error = None
        base_session_id = fetch_next_session_job_id()

        for attempt in range(max_attempts):
            session_id = base_session_id + attempt

            try:
                insert_job_stats_record(session_id)
                return session_id
            except oracledb.IntegrityError as error:
                if not is_unique_constraint_error(error):
                    raise
                last_error = error

        if last_error:
            raise last_error

        raise RuntimeError("Failed to reserve a unique job id.")


def fetch_file_status_rows():
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT *
                FROM PRC_.job_stats
                ORDER BY session_id DESC
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


def fetch_file_status_by_session_id(session_id):
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT *
                FROM PRC_.job_stats
                WHERE session_id = :session_id
            """, {"session_id": session_id})

            row = cursor.fetchone()
            if not row:
                return None

            columns = [col[0].lower() for col in cursor.description]
            return {
                columns[index]: serialize_db_value(value)
                for index, value in enumerate(row)
            }
