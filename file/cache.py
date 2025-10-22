import logging
import pathlib
from typing import List

from podcast.pod import Podcast


def get_uuid_in_cache_dir(directory: str, log: logging.Logger) -> List[str | None]:
    try:
        return [str(x.name) for x in pathlib.Path(directory).glob("*")]
    except FileNotFoundError as e:
        log.error(f"Failed to get uuids from cache dir {e}")
        return [None]


def prep_cache_dir(directory: str, log: logging.Logger):
    try:
        pathlib.Path(directory).mkdir(exist_ok=True)
        log.info(f"Cache dir {directory} OK")
    except (FileNotFoundError, OSError) as e:
        log.error(f"Failed to create or locate cache dir {e}")
        raise SystemExit


def return_cached_state(pod: Podcast, cached_uuids: List[str]) -> Podcast:
    if pod.uuid in cached_uuids:
        pod.downloaded = True
        return pod
    return pod
