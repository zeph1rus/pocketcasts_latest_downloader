import logging
import os
import pathlib
import sqlite3
import shutil
from dataclasses import dataclass
from datetime import datetime, timezone
from os import path
from typing import List
import httpx
from dotenv import load_dotenv

# Constants you can play with
DB_FILE = "pc_play.db"
CACHE_DIR = "cache"
OUTPUT_DIR = "output"
EPISODES_TO_GET = 30
M3U_FILENAME = "playlist.m3u"
TOKEN_EXPIRY_SECS = 7200
MINIMUM_EPISODE_LENGTH_MINS = 14

# Logging setup
LOGGER = logging.getLogger(__name__)
logging.basicConfig(level=logging.WARNING)

# PocketCasts API Endpoints
LATEST_EPISODES_API_ENDPOINT = "https://api.pocketcasts.com/user/new_releases"
LOGIN_URL = "https://api.pocketcasts.com/user/login"

BANNED_CHARS = [""" """, ".",  ",", "*", ":", "!", "?", "$", "@", "(", ")", "/", "\\", "'"]

@dataclass
class AuthData:
    token: str | None
    expires: int | None


@dataclass
class Podcast:
    uuid: str
    podcast: str
    title: str
    url: str
    downloaded: bool


def is_long_enough(secs: int) -> bool:
    return secs >= MINIMUM_EPISODE_LENGTH_MINS * 60


def filter_length(episode: dict) -> bool:
    if is_long_enough(episode.get("duration", 0)):
        return True
    return False


def create_db():
    LOGGER.info("Creating db")
    conn = sqlite3.connect(DB_FILE)
    try:
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute(
            """CREATE TABLE IF NOT EXISTS auth(name TEXT, token TEXT, expires INTEGER)"""
        )
        conn.commit()
        LOGGER.info("DB created")
    except sqlite3.DatabaseError as e:
        LOGGER.error(f"Couldn't create db {e}")
        raise SystemExit
    finally:
        conn.close()


def get_token_from_db() -> AuthData:
    LOGGER.info("Getting auth token from db")
    conn = sqlite3.connect(DB_FILE)
    try:
        c = conn.cursor()
        c.execute('''SELECT token, expires FROM auth WHERE name = "pocketcasts"''')
        if res := c.fetchone():
            return AuthData(token=res[0], expires=res[1])
        else:
            LOGGER.warning("No token found in db")
            return AuthData(token=None, expires=None)
    except sqlite3.DatabaseError as e:
        LOGGER.error(f"Couldn't get token from db {e}")
        return AuthData(token=None, expires=None)
    finally:
        conn.close()


# noinspection SqlWithoutWhere
# This is fine here - we want to wipe the table.
def save_token_to_db(token: str, expires: int) -> bool:
    LOGGER.info("Saving auth token to db")
    conn = sqlite3.connect(DB_FILE)
    try:
        c = conn.cursor()
        c.execute('''DELETE FROM auth''')
        c.execute('''INSERT INTO auth (name, token, expires) VALUES ("pocketcasts", ?, ?)''', (token, expires))
        conn.commit()
        return True
    except sqlite3.DatabaseError as e:
        LOGGER.error(f"Couldn't save token to db {e}")
        return False
    finally:
        conn.close()


def authenticate(username, password) -> str | None:
    LOGGER.info("Authenticating")

    login_params = {
        "email":    username,
        "password": password,
        "scope":    "webplayer"
    }

    auth_data = get_token_from_db()
    LOGGER.debug(auth_data)
    if auth_data.token and auth_data.expires:
        LOGGER.info("Token found in db")
        if auth_data.expires > int(datetime.now(timezone.utc).timestamp()):
            LOGGER.info("Token is still valid")
            return auth_data.token
        else:
            LOGGER.warning("Token expired")

    LOGGER.info("Requesting new token")
    login_request = httpx.post(LOGIN_URL, json=login_params)
    if login_request.status_code == 200:
        try:
            token = login_request.json().get("token")
            expires = int(datetime.now(timezone.utc).timestamp() + TOKEN_EXPIRY_SECS)
            save_token_to_db(token, expires)
            return token
        except (ValueError, KeyError) as e:
            LOGGER.error(f"{login_request.content}")
            LOGGER.error(f"Failed to get token {e}")
            return None
    else:
        logging.error(f"Failed to authenticate {login_request.status_code}, {login_request.text}")
    return None


def get_latest_episodes(token: str) -> None | list[None] | list[Podcast]:
    if token:
        headers = {
            "Authorization": f"Bearer {auth_token}",
        }
        try:

            latest_eps = httpx.post(LATEST_EPISODES_API_ENDPOINT, headers=headers).json()
            logging.info("Got latest Podcasts")

            print(f"Got {len(latest_eps.get('episodes', []))} episodes")
            long_enough_eps = list(filter(filter_length, latest_eps.get("episodes", [])))
            print(f"Episodes that are long enough: {len(long_enough_eps)}")
            logging.debug(long_enough_eps)
            target_episodes = latest_eps.get('episodes')[:EPISODES_TO_GET]
            logging.debug(f"Got latest episodes {target_episodes}")
            podcasts = []
            for ep in target_episodes:
                logging.debug(ep)
                logging.debug(f"Adding episode {ep.get('title')}")
                podcasts.append(Podcast(uuid=ep.get("uuid"),
                                        podcast=ep.get("podcastTitle"),
                                        title=ep.get("title"),
                                        url=ep.get("url"),
                                        downloaded=False))

            return podcasts
        except httpx.HTTPError as e:
            LOGGER.error(f"Failed to get latest episodes {e}")
    return [None]


def get_uuid_in_cache_dir(directory: str) -> List[str | None]:
    try:
        return [str(x.name) for x in pathlib.Path(directory).glob("*")]
    except FileNotFoundError as e:
        LOGGER.error(f"Failed to get uuids from cache dir {e}")
        return [None]


def prep_cache_dir(directory: str):
    try:
        pathlib.Path(directory).mkdir(exist_ok=True)
        LOGGER.info(f"Cache dir {directory} OK")
    except (FileNotFoundError, OSError) as e:
        LOGGER.error(f"Failed to create or locate cache dir {e}")
        raise SystemExit


def return_cached_state(pod: Podcast, cached_uuids: List[str]) -> Podcast:
    if pod.uuid in cached_uuids:
        pod.downloaded = True
        return pod
    return pod


def download_podcast(pod: Podcast, cache_dir: str) -> bool:
    try:
        with httpx.stream("GET", pod.url, follow_redirects=True) as r:
            LOGGER.info(f"Downloading {r.url}")
            with open(path.join(cache_dir, pod.uuid), "wb") as f:
                for chunk in r.iter_bytes():
                    f.write(chunk)
        return True
    except (httpx.HTTPError, FileNotFoundError, OSError) as e:
        LOGGER.error(f"Failed to download podcast {e}")
        return False


def create_output_dir_if_not_exists(directory: str):
    try:
        pathlib.Path(directory).mkdir(exist_ok=True)
    except (FileNotFoundError, OSError) as e:
        LOGGER.error(f"Failed to create output dir {e}")
        raise SystemExit


def remove_spaces_from_string(s: str) -> str:
    safer_string = s
    for banned_char in BANNED_CHARS:
        safer_string = safer_string.replace(banned_char, "_")
    return safer_string


def clear_output_dir(directory: str):
    try:
        for output_file in pathlib.Path(directory).glob("*"):
            if output_file.is_file():
                output_file.unlink()
    except (FileNotFoundError, OSError) as e:
        LOGGER.error(f"Failed to clear output dir {e}")
        raise SystemExit


def copy_pod_to_output_dir(pod: Podcast, output_dir: str, index: int) -> bool:
    try:
        print(f"Copying: {pod.podcast} - {pod.title} to output dir")
        shutil.copyfile(path.join(CACHE_DIR, pod.uuid),
                        path.join(output_dir,
                                  f"{remove_spaces_from_string(f'{index:03} {pod.podcast} {pod.title}')}.MP3")
                        )
        return True
    except (FileNotFoundError, OSError) as e:
        LOGGER.error(f"Failed to copy podcast to output dir {e}")
        return False


def create_m3u_file(output_dir: str, filename: str):
    try:
        with open(path.join(output_dir, filename), "w") as f:
            f.write("#EXTM3U\n")
            for output_file in sorted(
                    pathlib.Path(output_dir).glob("*.mp3")
            ):
                f.write(f"{output_file.name}\n")
    except (FileNotFoundError, OSError, IOError) as e:
        LOGGER.error(f"Failed to create m3u file {e}")
        raise SystemExit


if __name__ == '__main__':
    LOGGER.setLevel(logging.ERROR)
    load_dotenv()
    prep_cache_dir(CACHE_DIR)

    try:
        if not path.exists(DB_FILE):
            LOGGER.warning("DB doesn't exist, creating")
            create_db()
    except (IOError, FileNotFoundError, OSError) as failed_db_init:
        print(f"Failed to locate or create db {failed_db_init}")
        raise SystemExit
    LOGGER.info("DB exists")

    LOGGER.info("Creating output dir")
    create_output_dir_if_not_exists(OUTPUT_DIR)

    LOGGER.info("Clearing output dir")
    clear_output_dir(OUTPUT_DIR)

    LOGGER.info("Getting Initial Auth Token")
    auth_token = authenticate(os.getenv("PC_USERNAME"),
                              os.getenv("PC_PASSWORD"))
    if not auth_token:
        LOGGER.error("Failed to authenticate")
        raise SystemExit

    print("Authenticated with PocketCasts")

    # Get lastest EPISODES_TO_GET episodes
    latest = get_latest_episodes(auth_token)
    print(f"Selected newest {EPISODES_TO_GET} episodes")
    # Get list of cached episodes from cache directory
    cached_eps = (get_uuid_in_cache_dir(CACHE_DIR))

    # Check if the latest episodes are already in cache
    check_if_downloaded = map(lambda x: return_cached_state(x, cached_eps), latest)

    # Get the episodes that haven't been downloaded
    to_download = filter(lambda x: not x.downloaded, check_if_downloaded)

    print("Downloading undownloaded podcasts")
    for podcast_ep in to_download:
        logging.info(f"Downloading {podcast_ep.url}")
        print(f"Downloading {podcast_ep.podcast} - {podcast_ep.title}")
        download_podcast(podcast_ep, CACHE_DIR)

    i = 1
    for podcast_ep in latest:
        if copy_pod_to_output_dir(podcast_ep, OUTPUT_DIR, i):
            i += 1
        else:
            LOGGER.error(f"Failed to copy {podcast_ep.title} to output dir")
            raise SystemExit

    print("Creating m3u Playlist")
    create_m3u_file(OUTPUT_DIR, M3U_FILENAME)
