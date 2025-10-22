import logging
from dataclasses import dataclass

import httpx

from podcast.pod import Podcast


@dataclass
class Episode:
    uuid: str
    podcast_uuid: str
    podcast: Podcast
    title: str
    url: str
    duration: int
    number: int
    downloaded: bool = False


def get_single_podcast_episodes(token: str, uuid: str) -> list[Episode | None]:
    log = logging.getLogger(__name__)
    log.info("Getting Single podcast episodes")
    episodes = []
    api_url = f"https://podcast-api.pocketcasts.com/podcast/full/{uuid}"
    if token:
        headers = {
            "Authorization": f"Bearer {token}",
        }

        try:
            eps = httpx.post(api_url, headers=headers).json()
            if pod := eps.get("podcast"):
                for e in pod.get("episodes"):
                    episodes.append(Episode(
                            uuid=e.get("uuid"),
                            podcast_uuid=pod.get("uuid"),
                            podcast=pod.get("title"),
                            title=e.get("title"),
                            url=e.get("url"),
                            duration=e.get("duration"),
                            number=e.get("number"),
                    ))
            return episodes
        except (httpx.HTTPError, ValueError, TypeError) as episodes_error:
            log.error(f"{episodes_error}")
            return episodes
    return []
