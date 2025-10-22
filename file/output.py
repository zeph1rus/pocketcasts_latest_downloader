import pathlib
import shutil
from os import path

import taglib

from main import logger, CACHE_DIR
from podcast.pod import Podcast
from utils.common import remove_spaces_from_string


def create_output_dir_if_not_exists(directory: str):
    try:
        pathlib.Path(directory).mkdir(exist_ok=True)
    except (FileNotFoundError, OSError) as e:
        logger.error(f"Failed to create output dir {e}")
        raise SystemExit


def clear_output_dir(directory: str):
    try:
        for output_file in pathlib.Path(directory).glob("*"):
            if output_file.is_file():
                output_file.unlink()
    except (FileNotFoundError, OSError) as e:
        logger.error(f"Failed to clear output dir {e}")
        raise SystemExit


def copy_pod_to_output_dir(pod: Podcast, output_dir: str, index: int) -> bool:
    try:
        filename = f"{remove_spaces_from_string(f'{index:03} {pod.podcast} {pod.title}')}.MP3"
        print(f"Copying: {pod.podcast} - {pod.title} to output dir")
        shutil.copyfile(path.join(CACHE_DIR, pod.uuid),
                        path.join(output_dir, filename)
                        )
        with taglib.File(path.join(output_dir, filename), save_on_exit=True) as mp3_file:
            print(pod.podcast, pod.title)
            mp3_file.tags["TITLE"] = f"{index:03}-{pod.title}={pod.podcast}"
            mp3_file.tags["TOA"] = pod.podcast
            mp3_file.tags["PCS"] = "1"
            mp3_file.tags["TRK"] = f"{index:02}"
            mp3_file.tags["TAL"] = "PODCASTS"
        return True
    except (FileNotFoundError, OSError) as e:
        logger.error(f"Failed to copy podcast to output dir {e}")
        return False


def create_m3u_file(output_dir: str, filename: str):
    try:
        with open(path.join(output_dir, filename), "w") as f:
            f.write("#EXTM3U\n")
            for output_file in sorted(
                    pathlib.Path(output_dir).glob("*.mp3")
            ):
                f.write(f"{output_file.name}\n")
    except (FileNotFoundError, OSError, IOError) as e:
        logger.error(f"Failed to create m3u file {e}")
        raise SystemExit
