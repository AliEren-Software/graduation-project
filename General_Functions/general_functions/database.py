"""Oracle operations for the latest ODI job session."""

from .config import Settings


LATEST_SESSION_SQL = "SELECT MAX(session_id) FROM PRC_.job_stats"
UPDATE_CLOUD_STATUS_SQL = """
    UPDATE PRC_.job_stats SET cloud_status = 'success' WHERE session_id = :session_id
"""
ODI_STATUS_SQL = """
    SELECT
        s.SESS_NO,
        CASE
            WHEN s.SESS_STATUS = 'D' THEN 'SUCCESS'
            WHEN s.SESS_STATUS = 'E' THEN 'ERROR'
            WHEN s.SESS_STATUS = 'M' THEN 'WARNING'
            ELSE s.SESS_STATUS
        END AS STATUS,
        MAX(
            CASE
                WHEN t.TASK_STATUS = 'E' THEN DBMS_LOB.SUBSTR(t.ERROR_MESSAGE, 4000, 1)
            END
        ) AS ERROR_MESSAGE
    FROM DEV_ODI_REPO.SNP_SESSION s
    LEFT JOIN DEV_ODI_REPO.SNP_SESS_TASK_LOG t ON s.SESS_NO = t.SESS_NO
    WHERE s.SESS_NO = :sess_no
    GROUP BY s.SESS_NO, s.SESS_STATUS
"""
UPDATE_ODI_CLEANING_SQL = """
    UPDATE PRC_.job_stats SET ODI_CLEANING = :odi_cleaning WHERE session_id = :session_id
"""
# The column spelling matches the existing Oracle schema.
UPDATE_ODI_ERROR_MESSAGE_SQL = """
    UPDATE PRC_.job_stats SET ODI_ERROR_MESAGE = :odi_error_mesage
    WHERE session_id = :session_id
"""


def get_connection(settings: Settings):
    try:
        import oracledb
    except ImportError as error:
        raise RuntimeError("Install dependencies from requirements.txt") from error
    dsn = oracledb.makedsn(
        settings.oracle_host, settings.oracle_port, service_name=settings.oracle_service_name
    )
    return oracledb.connect(
        user=settings.oracle_user,
        password=settings.oracle_password,
        dsn=dsn,
    )


def latest_session_id(cursor):
    cursor.execute(LATEST_SESSION_SQL)
    row = cursor.fetchone()
    session_id = row[0] if row else None
    if session_id is None:
        raise RuntimeError("PRC_.job_stats has no session_id")
    return session_id


def update_latest_odi_cleaning_status(settings: Settings):
    connection = get_connection(settings)
    try:
        with connection.cursor() as cursor:
            session_id = latest_session_id(cursor)
            cursor.execute(ODI_STATUS_SQL, sess_no=session_id)
            row = cursor.fetchone()
            if row is None:
                raise RuntimeError(f"No ODI session found for sess_no={session_id}")
            status = row[1]
            cursor.execute(UPDATE_ODI_CLEANING_SQL, odi_cleaning=status, session_id=session_id)
            if status in {"ERROR", "SUCCESS"}:
                cursor.execute(
                    UPDATE_ODI_ERROR_MESSAGE_SQL,
                    odi_error_mesage=status,
                    session_id=session_id,
                )
        connection.commit()
        return session_id, status
    finally:
        connection.close()


def mark_latest_cloud_status_only_success(settings: Settings):
    connection = get_connection(settings)
    try:
        with connection.cursor() as cursor:
            session_id = latest_session_id(cursor)
            cursor.execute(UPDATE_CLOUD_STATUS_SQL, session_id=session_id)
        connection.commit()
        return session_id
    finally:
        connection.close()
