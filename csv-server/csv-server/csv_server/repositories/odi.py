from ..db import get_connection
from ..utils import clean_error_message


def get_session_status(sess_no):
    try:
        with get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("""
                    SELECT
                        s.SESS_NO,
                        CASE
                            WHEN s.SESS_STATUS = 'D' THEN 'SUCCESS'
                            WHEN s.SESS_STATUS = 'E' THEN 'ERROR'
                            WHEN s.SESS_STATUS = 'M' THEN 'WARNING'
                            ELSE s.SESS_STATUS
                        END AS STATUS,
                        MAX(CASE
                            WHEN t.TASK_STATUS = 'E' THEN
                                DBMS_LOB.SUBSTR(t.ERROR_MESSAGE, 4000, 1)
                        END) AS ERROR_MESSAGE
                    FROM DEV_ODI_REPO.SNP_SESSION s
                    LEFT JOIN DEV_ODI_REPO.SNP_SESS_TASK_LOG t
                        ON s.SESS_NO = t.SESS_NO
                    WHERE s.SESS_NO = :sess_no
                    GROUP BY s.SESS_NO, s.SESS_STATUS
                """, {"sess_no": sess_no})
                row = cursor.fetchone()

                if not row:
                    return None

                session_id, status, error_message = row

                if status == "SUCCESS":
                    return {
                        "job_id": session_id,
                        "job_status": "success",
                    }

                if status == "ERROR":
                    return {
                        "job_id": session_id,
                        "job_status": "failed",
                        "error_message": clean_error_message(error_message),
                    }

                return {
                    "job_id": session_id,
                    "job_status": "processing",
                }
    except Exception as error:
        return {
            "job_status": "failed",
            "error_message": str(error),
        }
