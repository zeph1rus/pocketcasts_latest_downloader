from dataclasses import dataclass

import httpx

from main import MINIMUM_EPISODE_LENGTH_MINS, logger, auth_token


@dataclass
class Episode:
    uuid: str
    podcast_uuid: str
    title: str
    url: str
    duration: int
    number: int


def is_long_enough(secs: int) -> bool:
    return secs >= MINIMUM_EPISODE_LENGTH_MINS * 60


def filter_length(episode: dict) -> bool:
    if is_long_enough(episode.get("duration", 0)):
        return True
    return False


def get_single_podcast_episodes(token: str, uuid: str) -> list[Episode] | None:
    logger.info("Getting Single podcast episodes")
    episodes = []
    api_url = f"https://podcast-api.pocketcasts.com/podcast/full/{uuid}"
    if token:
        headers = {
            "Authorization": f"Bearer {auth_token}",
        }

        try:
            eps = httpx.post(api_url, headers=headers).json()
            if pod := eps.get("podcast"):
                for e in pod.get("episodes"):
                    episodes.append(Episode(
                            uuid=e.get("uuid"),
                            podcast_uuid=pod.get("uuid"),
                            title=e.get("title"),
                            url=e.get("url"),
                            duration=e.get("duration"),
                            number=e.get("number"),
                    ))
            return episodes
        except (httpx.HTTPError, ValueError, TypeError) as episodes_error:
            logger.error(f"{episodes_error}")
            return episodes
