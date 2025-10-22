import logging
import os

from dotenv import load_dotenv

from auth.auth import authenticate
from file.cache import get_uuid_in_cache_dir, prep_cache_dir, return_cached_state
from file.output import create_output_dir_if_not_exists, clear_output_dir, copy_pod_to_output_dir, create_m3u_file
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

# PocketCasts API Endpoints
LATEST_EPISODES_API_ENDPOINT = "https://api.pocketcasts.com/user/new_releases"
LOGIN_URL = "https://api.pocketcasts.com/user/login"

# noinspection SqlWithoutWhere
# This is fine here - we want to wipe the table.


if __name__ == '__main__':
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.ERROR)

    load_dotenv()
    prep_cache_dir(CACHE_DIR)

    logger.info("Creating output dir")
    create_output_dir_if_not_exists(OUTPUT_DIR)

    logger.info("Clearing output dir")
    clear_output_dir(OUTPUT_DIR)

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
            logger.error(f"Failed to copy {podcast_ep.title} to output dir")
            raise SystemExit

    print("Creating m3u Playlist")
    create_m3u_file(OUTPUT_DIR, M3U_FILENAME)
