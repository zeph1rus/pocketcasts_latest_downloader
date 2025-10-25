import logging
import pathlib
import shutil
from os import path

import taglib

from podcast.episodes import Episode
from podcast.pod import Podcast
from utils.common import remove_spaces_from_string


def create_output_dir_if_not_exists(directory: str, log: logging.Logger):
    try:
        pathlib.Path(directory).mkdir(exist_ok=True)
    except (FileNotFoundError, OSError) as e:
        log.error(f"Failed to create output dir {e}")
        raise SystemExit


def clear_output_dir(directory: str, log: logging.Logger):
    try:
        for output_file in pathlib.Path(directory).glob("*"):
            if output_file.is_file():
                output_file.unlink()
    except (FileNotFoundError, OSError) as e:
        log.error(f"Failed to clear output dir {e}")
        raise SystemExit


def tag_file(pod: Podcast | Episode, output_dir: str, filename: str, index: int):
    with taglib.File(path.join(output_dir, filename), save_on_exit=True) as mp3_file:
        print(f"Tagging {pod.podcast}, {pod.title}")
        mp3_file.tags["TITLE"] = f"{index:03}-{pod.title}={pod.podcast}"
        mp3_file.tags["TOA"] = pod.podcast
        mp3_file.tags["PCS"] = "1"
        mp3_file.tags["TRK"] = f"{index:02}"
        mp3_file.tags["TAL"] = "PODCASTS"


def copy_pod_to_output_dir(pod: Podcast | Episode,
                           output_dir: str,
                           cache_dir: str,
                           index: int, log: logging.Logger,
                           retag_files: int = False) -> bool:
    try:
        filename = f"{remove_spaces_from_string(f'{index:03} {pod.podcast} {pod.title}')}.MP3"
        print(f"Copying: {pod.podcast} - {pod.title} to output dir")
        shutil.copyfile(path.join(cache_dir, pod.uuid),
                        path.join(output_dir, filename)
                        )
        if retag_files:
            tag_file(pod, output_dir, filename, index)
        return True
    except (FileNotFoundError, OSError) as e:
        log.error(f"Failed to copy podcast to output dir {e}")
        return False


def create_m3u_file(output_dir: str, filename: str):
    log = logging.getLogger("__NAME__")
    try:
        with open(path.join(output_dir, filename), "w") as f:
            f.write("#EXTM3U\n")
            for output_file in sorted(
                    pathlib.Path(output_dir).glob("*.mp3", case_sensitive=False),
            ):
                f.write(f"{output_file.name}\n")
    except (FileNotFoundError, OSError, IOError) as e:
        log.error(f"Failed to create m3u file {e}")
        raise SystemExit


def copy_files(latest: list[Podcast | Episode], output_dir: str, cache_dir: str, retag_files: bool = False):
    logger = logging.getLogger("__name__")
    logger.info("Creating output dir")

    clear_output_dir(output_dir, logger)
    create_output_dir_if_not_exists(output_dir, logger)

    index = 1

    logger.info("Clearing output dir")

    for podcast_ep in latest:
        if copy_pod_to_output_dir(podcast_ep, output_dir, cache_dir, index, logger, retag_files):
            index += 1
        else:
            logger.error(f"Failed to copy {podcast_ep.title} to output dir")
            raise SystemExit
