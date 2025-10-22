import logging
from dataclasses import dataclass

import httpx

from utils.common import filter_length

LATEST_EPISODES_API_ENDPOINT = "https://api.pocketcasts.com/user/new_releases"


@dataclass
class Podcast:
    uuid: str
    podcast: str
    title: str
    url: str
    duration: int
    downloaded: bool


def get_latest_episodes(token: str, filter_on_min_length: bool, min_length: int, number_of_episodes: int) -> list[Podcast | None]:
    log = logging.getLogger(__name__)
    if token:
        headers = {
            "Authorization": f"Bearer {token}",
        }
        try:

            latest_eps = httpx.post(LATEST_EPISODES_API_ENDPOINT, headers=headers).json()
            log.info("Got latest Podcasts")

            print(f"Got {len(latest_eps.get('episodes', []))} episodes")

            episode_list = latest_eps.get('episodes', [])

            filter_expr = lambda x: filter_length(x.get("duration", 0), min_length)

            if filter_on_min_length:
                episode_list = list(
                        filter(
                                filter_expr,
                                episode_list))

            print(f"Episodes that are long enough: {len(episode_list)}")
            log.debug(episode_list)

            target_episodes = episode_list.get('episodes')[:number_of_episodes]

            logging.debug(f"Got latest episodes {target_episodes}")
            podcasts = []
            for ep in target_episodes:
                log.debug(ep)
                log.debug(f"Adding episode {ep.get('title')}")
                podcasts.append(Podcast(uuid=ep.get("uuid"),
                                        podcast=ep.get("podcastTitle"),
                                        title=ep.get("title"),
                                        url=ep.get("url"),
                                        duration=ep.get("duration"),
                                        downloaded=False))

            return podcasts
        except httpx.HTTPError as e:
            log.error(f"Failed to get latest episodes {e}")
    return []
