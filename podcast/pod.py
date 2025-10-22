import logging
from dataclasses import dataclass

import httpx

from main import auth_token, LATEST_EPISODES_API_ENDPOINT, EPISODES_TO_GET, logger
from podcast.episodes import filter_length


@dataclass
class Podcast:
    uuid: str
    podcast: str
    title: str
    url: str
    downloaded: bool


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
            logger.error(f"Failed to get latest episodes {e}")
    return [None]
