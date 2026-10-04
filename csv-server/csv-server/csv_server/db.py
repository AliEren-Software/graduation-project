"""Oracle connection boundary for repositories."""

import oracledb

from . import config


DSN = oracledb.makedsn(config.ORACLE_HOST, config.ORACLE_PORT, sid=config.ORACLE_SID)


def get_connection():
    return oracledb.connect(
        user=config.ORACLE_USER,
        password=config.ORACLE_PASSWORD,
        dsn=DSN,
    )
