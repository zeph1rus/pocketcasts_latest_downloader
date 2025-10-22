import logging

from os import path

import httpx

from podcast.pod import Podcast


def download_podcast(pod: Podcast, cache_dir: str) -> bool:
    logger = logging.getLogger("__name__")
    try:
        with httpx.stream("GET", pod.url, follow_redirects=True) as r:
            logger.info(f"Downloading {r.url}")
            with open(path.join(cache_dir, pod.uuid), "wb") as f:
                for chunk in r.iter_bytes():
                    f.write(chunk)
        return True
    except (httpx.HTTPError, FileNotFoundError, OSError) as e:
        logger.error(f"Failed to download podcast {e}")
        return False
