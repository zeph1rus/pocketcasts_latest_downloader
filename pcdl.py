"""Pocketcasts Downloader.

By default, will download the latest podcasts from your new releases feed

Usage:
    pcdl.py [--podcast PODCAST_UUID] [--output PATH] [--retag] [--number NUMTODL] [--min-podcast-length MINUTES] [--m3u-filename FILENAME] [--clear-cache] [--clear-out]
    pcdl.py (-h | --help)

Options:
    --podcast PODCAST_UUID           Podcast UUID from Pocketcasts. If this is supplied we will just download the latest podcast from this single podcast
    --output PATH                    Output path (relative or absolute) of the resulting downloaded files [default: output]
    --retag                          Rewrite ID3 Tags to allow easier sorting on mp3 players with limited capabilities (format: {sequencen no}-{episode name}) [default: False]
    --number NUMTODL                 Number of episodes to download [default: 30]
    --min-podcast-length MINUTES     Only download podcasts longer than this many minutes, to avoid downloading preview episodes etc
    --m3u-filename FILENAME          Name of the m3u file created in the output directory [default: playlist.m3u]
    --clear-cache                    Clear cache as the files are being copied to the output dir
    --clear-out                      Clears output dir
    -h --help                        Show this help message

"""

import logging
import os

import docopt
from dotenv import load_dotenv

from auth.auth import authenticate
from file.cache import get_uuid_in_cache_dir, prep_cache_dir, return_cached_state
from file.output import create_m3u_file, create_output_dir_if_not_exists, copy_pod_to_output_dir, clear_output_dir
from net.download import download_podcast
from podcast.episodes import get_single_podcast_episodes
from podcast.pod import get_latest_episodes


# Constants you can play with
DB_FILE = "pc_play.db"
CACHE_DIR = "cache"
TOKEN_EXPIRY_SECS = 7200

# PocketCasts API Endpoints
LOGIN_URL = "https://api.pocketcasts.com/user/login"

if __name__ == '__main__':
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.WARNING)
    cl_args = docopt.docopt(__doc__)
    OUTPUT_DIR = os.path.realpath(cl_args.get("--output") or "output")
    
    # Ensure output dir
    create_output_dir_if_not_exists(OUTPUT_DIR, logger)

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
    check_if_downloaded = list(map(lambda x: return_cached_state(x, cached_eps), latest))

    # Get the episodes that haven't been downloaded
    to_download = filter(lambda x: not x.downloaded, check_if_downloaded)
    downloaded = filter(lambda x: x.downloaded, check_if_downloaded)

    # Clears output dir
    if cl_args["--clear-out"]:
        clear_output_dir(OUTPUT_DIR, logger)

    # Copy cached
    for idx, podcast_ep in enumerate(downloaded):
        logging.info(f"Copying cached episode {podcast_ep.url} from {CACHE_DIR} to {os.path.realpath(OUTPUT_DIR)}")
        copy_pod_to_output_dir(podcast_ep, OUTPUT_DIR, CACHE_DIR, idx + 1, logger, cl_args.get("--retag"), cl_args["--clear-cache"])

    print("Downloading undownloaded podcasts")
    for idx, podcast_ep in enumerate(to_download):
        logging.info(f"Downloading {podcast_ep.url}")
        print(f"Downloading {podcast_ep.podcast} - {podcast_ep.title}")
        download_podcast(podcast_ep, CACHE_DIR)
        copy_pod_to_output_dir(podcast_ep, OUTPUT_DIR, CACHE_DIR, idx + 1, logger, cl_args.get("--retag"), cl_args["--clear-cache"])


    print("Creating m3u Playlist")
    create_m3u_file(os.path.realpath(OUTPUT_DIR), m3u_filename)
