# Pocketcasts Latest Downloader

This script downloads the latest number (default 10) podcasts from your Pocketcasts Plus "New Releases" feed.

It then puts the in a folder and creates an M3U playlist file for them, they are named sequentially.

This is written to simplify stuffing podcasts onto dumb sports MP3 players, that are waterproof or similar for swimming and exercise.

## Requirements

Python 3.13 or later. 

An understanding of how to run a Python script from the command line.

## Installation

1. Clone this repository
2. Install UV https://docs.astral.sh/uv/getting-started/installation/
3. Create a .env file (see example) or set the environment variables in your shell for Username/Password


## Usage

Run the script with `uv run main.py` - all dependencies will be installed at this point. 

The files and playlist are contained in the `output` folder. This can be changed by editing the script.

Copy the files from there onto your player.  I've included the script I use as `transfer.sh`

## Usage

By default, will download the latest podcasts from your new releases feed
```
Usage:
    pcdl.py [--podcast=PODCAST_UUID] [--retag] [--number=NUMTODL] [ --min-podcast-length MINUTES] [--m3u-filename FILENAME]
    pcdl.py (-h | --help)

Options:
    --podcast PODCAST_UUID           Podcast UUID from Pocketcasts. If this is supplied we will just 
                                     download the latest podcasts from this single podcast
    --retag                          Rewrite ID3 Tags to allow easier sorting on mp3 players with limited capabilities
                                     (format: {sequencen no}-{episode name}) [default: False]
    --number NUMTODL                 Number of episodes to download [default: 30]
    --min-podcast-length MINUTES     Only download podcasts longer than this many minutes, 
                                     to avoid downloading preview episodes etc
    --m3u-filename FILENAME          Name of the m3u file created in the output directory [default: playlist.m3u]
    -h --help                        Show this help message

```

You can change the following constants in the script.
    
```python
DB_FILE = "pc_play.db" # The sqlite database file to store the auth token
CACHE_DIR = "cache" # The cache directory to store the podcast files
OUTPUT_DIR = "output" # The output directory to store the playlist and files
TOKEN_EXPIRY_SECS = 7200 # The number of seconds the auth token is valid for (2 hours). It will be automatically refreshed
```