"""Pocketcasts Downloader.

By default, will download the latest podcasts from your new releases feed

Usage:
    pcdl.py [--podcast PODCAST_UUID] [--retag] [--number NUMTODL] [ --min-podcast-length MINUTES] [--m3u-filename FILENAME]
    pcdl.py (-h | --help)

Options:
    --podcast PODCAST_UUID           Podcast UUID from Pocketcasts. If this is supplied we will just download the latest podcast from this single podcast
    --retag                          Rewrite ID3 Tags to allow easier sorting on mp3 players with limited capabilities (format: {sequencen no}-{episode name}) [default: False]
    --number NUMTODL                 Number of episodes to download [default: 30]
    --min-podcast-length MINUTES     Only download podcasts longer than this many minutes, to avoid downloading preview episodes etc
    --m3u-filename FILENAME          Name of the m3u file created in the output directory [default: playlist.m3u]
    -h --help                        Show this help message

"""

import logging
import os

import docopt
from dotenv import load_dotenv

from auth.auth import authenticate
from file.cache import get_uuid_in_cache_dir, prep_cache_dir, return_cached_state
from file.output import create_m3u_file, copy_files
from net.download import download_podcast
from podcast.episodes import get_single_podcast_episodes
from podcast.pod import get_latest_episodes

# Constants you can play with
DB_FILE = "pc_play.db"
CACHE_DIR = "cache"
OUTPUT_DIR = "output"
TOKEN_EXPIRY_SECS = 7200

# PocketCasts API Endpoints
LOGIN_URL = "https://api.pocketcasts.com/user/login"

if __name__ == '__main__':
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.WARNING)
    cl_args = docopt.docopt(__doc__)


    min_ep_length = cl_args["--min-podcast-length"]
    if min_ep_length:
        print(f"Minimum episode length: {min_ep_length}")

    num_to_get = int(cl_args["--number"])
    print(f"Number of episodes to download: {num_to_get}")

    m3u_filename = cl_args["--m3u-filename"]

    podcast_uuid = cl_args["--podcast"]
    if podcast_uuid:
        print(f"Using episodes from Podcast UUID: {podcast_uuid}")

    do_retag = cl_args["--retag"]
    if do_retag:
        print(f"Episodes will be retagged with new ID3 Tags")

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

    print(podcast_uuid)
    latest = []

    if podcast_uuid is not None:
        print(f"Getting latest podcasts from Podcast: {podcast_uuid}")
        latest = get_single_podcast_episodes(auth_token,
                                         podcast_uuid,
                                         True if min_ep_length else False,
                                         min_ep_length,
                                         num_to_get)

    else:
        print("Downloading Latest Podcasts from New Releases")
        latest = get_latest_episodes(auth_token,
                                     True if min_ep_length else False,
                                     min_ep_length,
                                     num_to_get)

    if latest == []:
        logger.error("Failed to get episodes")
        raise SystemExit

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

    copy_files(latest, OUTPUT_DIR, CACHE_DIR, cl_args.get("--retag"))

    print("Creating m3u Playlist")
    create_m3u_file(os.path.realpath(OUTPUT_DIR), m3u_filename)
