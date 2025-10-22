import logging
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from os import path

import httpx


@dataclass
class AuthData:
    token: str | None
    expires: int | None


def create_db(db_path: str, log: logging.Logger) -> None:
    log.info("Creating db")
    conn = sqlite3.connect(db_path)
    try:
        conn = sqlite3.connect(db_path)
        c = conn.cursor()
        c.execute(
                """CREATE TABLE IF NOT EXISTS auth(name TEXT, token TEXT, expires INTEGER)"""
        )
        conn.commit()
        log.info("DB created")
    except sqlite3.DatabaseError as e:
        log.error(f"Couldn't create db {e}")
        raise SystemExit
    finally:
        conn.close()


def get_token_from_db(db_path: str, log: logging.Logger) -> AuthData:
    log.info("Getting auth token from db")
    conn = sqlite3.connect(db_path)
    try:
        c = conn.cursor()
        c.execute('''SELECT token, expires FROM auth WHERE name = "pocketcasts"''')
        if res := c.fetchone():
            return AuthData(token=res[0], expires=res[1])
        else:
            log.warning("No token found in db")
            return AuthData(token=None, expires=None)
    except sqlite3.DatabaseError as e:
        log.error(f"Couldn't get token from db {e}")
        return AuthData(token=None, expires=None)
    finally:
        conn.close()


def save_token_to_db(db_path: str, token: str, expires: int, log: logging.Logger) -> bool:
    log.info("Saving auth token to db")
    conn = sqlite3.connect(db_path)
    try:
        c = conn.cursor()
        c.execute('''DELETE FROM auth''')
        c.execute('''INSERT INTO auth (name, token, expires) VALUES ("pocketcasts", ?, ?)''', (token, expires))
        conn.commit()
        return True
    except sqlite3.DatabaseError as e:
        log.error(f"Couldn't save token to db {e}")
        return False
    finally:
        conn.close()


def do_db_checks(db_path: str, log: logging.Logger):
    try:
        if not path.exists(db_path):
            log.warning("DB doesn't exist, creating")
            create_db(db_path, log)
    except (IOError, FileNotFoundError, OSError) as failed_db_init:
        print(f"Failed to locate or create db {failed_db_init}")
        raise SystemExit
    log.info("DB exists")


def authenticate(username, password, db_filepath, token_validity, login_url) -> str | None:

    logger = logging.getLogger("__name__")

    logger.info("Checking DB")
    do_db_checks(db_filepath, logger)

    logger.info("Authenticating")
    login_params = {
        "email":    username,
        "password": password,
        "scope":    "webplayer"
    }

    auth_data = get_token_from_db(db_filepath, logger)
    logger.debug(auth_data)
    if auth_data.token and auth_data.expires:
        logger.info("Token found in db")
        if auth_data.expires > int(datetime.now(timezone.utc).timestamp()):
            logger.info("Token is still valid")
            return auth_data.token
        else:
            logger.warning("Token expired")

    logger.info("Requesting new token")
    login_request = httpx.post(login_url, json=login_params)
    if login_request.status_code == 200:
        try:
            token = login_request.json().get("token")
            expires = int(datetime.now(timezone.utc).timestamp() + token_validity)
            save_token_to_db(db_filepath, token, expires, logger)
            return token
        except (ValueError, KeyError) as e:
            logger.error(f"{login_request.content}")
            logger.error(f"Failed to get token {e}")
            return None
    else:
        logger.error(f"Failed to authenticate {login_request.status_code}, {login_request.text}")
    return None
