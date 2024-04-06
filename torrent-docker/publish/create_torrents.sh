#!/bin/sh
#
# Creates a torrent for each file in a directory and for each directory
# within the directory a single torrent will be created.
#
# This means to have a torrent with multiple files provide a directory.
#
# usage:
#   create_torrents.sh [source-files] [torrent-directory]
[ $# -gt 0 ] && SOURCE="$1" || SOURCE="sources/"
[ $# -gt 1 ] && DESTINATION="$2" || DESTINATION="torrents/"

[ -z "$ANNOUNCE_URL" ] && ANNOUNCE_URL=http://localhost:6969/announce

# Create a torrent for each file.
#
# Don't create a torrent of a torrent file.
find "$SOURCE" -type f -maxdepth 1 -not -name "*.torrent" \
    -exec /usr/bin/mktorrent -a "$ANNOUNCE_URL" {} \;

 # Create a torrent for each directory.
#
# This enables a torrent to be created with multiple files.
find "$SOURCE" -type d -mindepth 1 -maxdepth 1 \
    -exec /usr/bin/mktorrent -a "$ANNOUNCE_URL" {} \;

echo Copying torrents to "$DESTINATION"
cp ./*.torrent "$DESTINATION"
