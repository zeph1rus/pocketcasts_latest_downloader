# Pocketcasts Latest Downloader

This script downloads the latest number (default: `30`) podcasts from your Pocketcasts Plus "New Releases" feed, or from a single podcast.

It then puts them in a folder and creates an M3U playlist file for them, they are named sequentially, and optionally retagged with ID3 tags that make it easier to sort on players with limited screen sizes.

This is written to simplify stuffing podcasts onto dumb sports MP3 players, that are waterproof or similar for swimming and exercise.

## Requirements

Python 3.13 or later,  uv python manager

An understanding of how to run a Python script from the command line.

## Installation

1. Clone this repository
2. Install UV https://docs.astral.sh/uv/getting-started/installation/
3. Create a .env file (see example) or set the environment variables in your shell for Username/Password


## Usage

Run the script with `uv run pcdl.py` - all dependencies will be installed at this point.  Please see the Usage section for options

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
                                     this helps to avoid downloading preview episodes etc.
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

## Troubleshooting

### It downloaded a podcast that wasn't long enough to match the filter 

This sometimes happens if the podcast has the duration set to 0 in pocketcasts.  Since we don't know how long it is it just gets downloaded.

### Error building on UBUNTU 24, `missing taglib/tstring.h: No such file or directory`

To fix this `apt install libtag1-dev` and then change the version of `pytaglib` in `pyproject.toml` to `"pytaglib==2.0.0"`

Then run `uv sync`.

This error happens because ubuntu 24 doesn't ship with taglib 2.0, and the pytaglib linux distribution doesn't have binary wheels. 

I'm going to fix this by switching to a different tagging library at some point. 