import logging
import os

from dotenv import load_dotenv
from auth.auth import authenticate
from file.cache import get_uuid_in_cache_dir, prep_cache_dir, return_cached_state
from file.output import create_m3u_file, copy_files
from net.download import download_podcast
from podcast.pod import get_latest_episodes

# Constants you can play with
DB_FILE = "pc_play.db"
CACHE_DIR = "cache"
OUTPUT_DIR = "output"
EPISODES_TO_GET = 30
M3U_FILENAME = "playlist.m3u"
TOKEN_EXPIRY_SECS = 7200
MINIMUM_EPISODE_LENGTH_MINS = 14
FILTER_LENGTH = True
RETAG_FILES = True

# PocketCasts API Endpoints
LOGIN_URL = "https://api.pocketcasts.com/user/login"

# noinspection SqlWithoutWhere
# This is fine here - we want to wipe the table.


if __name__ == '__main__':
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)

    load_dotenv()
    prep_cache_dir(CACHE_DIR, logger)
    cache_dir = get_uuid_in_cache_dir(CACHE_DIR, logger)

    logger.info("Getting Initial Auth Token")
    auth_token = authenticate(os.getenv("PC_USERNAME"),
                              os.getenv("PC_PASSWORD"),
                              DB_FILE,
                              TOKEN_EXPIRY_SECS,
                              LOGIN_URL
                              )
    if not auth_token:
        logger.error("Failed to authenticate")
        raise SystemExit

    print("Authenticated with PocketCasts")

    # Get lastest EPISODES_TO_GET episodes
    latest = get_latest_episodes(auth_token,
                                 FILTER_LENGTH,
                                 MINIMUM_EPISODE_LENGTH_MINS,
                                 EPISODES_TO_GET)

    print(f"Selected newest {EPISODES_TO_GET} episodes")
    # Get list of cached episodes from cache directory
    cached_eps = (get_uuid_in_cache_dir(CACHE_DIR, logger))

    # Check if the latest episodes are already in cache
    check_if_downloaded = map(lambda x: return_cached_state(x, cached_eps), latest)

    # Get the episodes that haven't been downloaded
    to_download = filter(lambda x: not x.downloaded, check_if_downloaded)

    print("Downloading undownloaded podcasts")
    for podcast_ep in to_download:
        logging.info(f"Downloading {podcast_ep.url}")
        print(f"Downloading {podcast_ep.podcast} - {podcast_ep.title}")
        download_podcast(podcast_ep, CACHE_DIR)

    copy_files(latest, OUTPUT_DIR, CACHE_DIR, RETAG_FILES)

    print("Creating m3u Playlist")
    create_m3u_file(OUTPUT_DIR, M3U_FILENAME)
