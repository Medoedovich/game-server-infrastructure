import logging
import os
import sqlite3
import time

import pymysql


SQLITE_PATH = os.getenv("SQLITE_PATH", "/data/LoginDatabase.db3")
DB_HOST = os.getenv("DB_HOST", "db")
DB_PORT = int(os.getenv("DB_PORT", "3306"))
DB_NAME = os.getenv("DB_NAME", "bf2stats")
DB_USER = os.environ["DB_USER"]
DB_PASSWORD = os.environ["DB_PASSWORD"]

INTERVAL = float(os.getenv("SYNC_INTERVAL", "1"))
DRY_RUN = os.getenv("DRY_RUN", "true").lower() == "true"

PROFILE_ID_OFFSET = 100000000

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)
log = logging.getLogger("player-sync")


def read_master_accounts():
    connection = sqlite3.connect(
        f"file:{SQLITE_PATH}?mode=ro",
        uri=True,
        timeout=5,
    )

    try:
        return connection.execute(
            "SELECT id, name FROM users ORDER BY id"
        ).fetchall()
    finally:
        connection.close()


def synchronize():
    accounts = read_master_accounts()
    matched = 0
    missing = 0
    conflicts = 0

    connection = pymysql.connect(
        host=DB_HOST,
        port=DB_PORT,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME,
        connect_timeout=5,
        read_timeout=5,
        write_timeout=5,
        autocommit=False,
    )

    try:
        with connection.cursor() as cursor:
            for account_id, name in accounts:
                pid = PROFILE_ID_OFFSET + account_id

                cursor.execute(
                    "SELECT id, name FROM player "
                    "WHERE id = %s OR name = %s",
                    (pid, name),
                )
                existing = cursor.fetchall()

                if existing:
                    if len(existing) == 1 and existing[0] == (pid, name):
                        matched += 1
                        continue

                    conflicts += 1
                    log.error(
                        "CONFLICT pid=%s name=%r existing=%r",
                        pid, name, existing,
                    )
                    continue

                missing += 1

                if DRY_RUN:
                    log.info(
                        "DRY-RUN: would create pid=%s name=%r",
                        pid, name,
                    )
                    continue

                cursor.execute(
                    "INSERT INTO player "
                    "(id, name, password, country, rank_id) "
                    "VALUES (%s, %s, %s, %s, %s)",
                    (pid, name, "", "xx", 0),
                )
                connection.commit()

                log.info(
                    "CREATED pid=%s name=%r",
                    pid, name,
                )
        if missing or conflicts:
            log.info(
                "SYNC SUMMARY: master=%s matched=%s missing=%s conflicts=%s",
                len(accounts), matched, missing, conflicts,
            )
    finally:
        connection.close()


def main():
    log.info(
        "Starting player-sync interval=%ss dry_run=%s",
        INTERVAL, DRY_RUN,
    )

    error_active = False
    last_error_log = 0.0

    while True:
        try:
            synchronize()

            if error_active:
                log.info("Synchronization recovered")
                error_active = False
                last_error_log = 0.0

        except Exception:
            now = time.monotonic()

            if not error_active or now - last_error_log >= 60:
                log.exception("Synchronization failed")
                last_error_log = now

            error_active = True

        time.sleep(INTERVAL)


if __name__ == "__main__":
    main()
