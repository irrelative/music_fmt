# Music Fmt

An agent that organizes music files. Assume a folder contains an album for an artist.

Rules:
* Single flac file + cue file should be split into track files, using the `flacue.py` tool
* All flac files should be converted to mp3, using the `flac2mp3.sh`
* All individual track files should be `{TRACK_NUMBER} - {TRACK_TITLE}.mp3`. Track numbers should be 2 digit and have leading `0` eg: `01 - Song Title.mp3`
* mp3 metadata should be updated using `picard`
* Album folder names should follow this convention: `{ALBUM_NAME} - ({ALBUM_YEAR})`

