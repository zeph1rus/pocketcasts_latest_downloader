#!/usr/bin/env bash

DESTINATION=/Volumes/AGP-S07/

if [ -d "$DESTINATION" ]; then
    rm -f $DESTINATION/*.mp3
    rm -f $DESTINATION/*.m3u
else
    echo "Destination not found"
    exit 1
fi

cp -v output/* $DESTINATION