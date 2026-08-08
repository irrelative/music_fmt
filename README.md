# music_fmt

`music_fmt` identifies albums with MusicBrainz and organizes an existing music
library into one predictable layout:

```text
Artist/
└── Album (Original Year)/
    ├── 01 - Track Title.mp3
    └── 02 - Track Title.flac
```

Multidisc releases use `CD 01`, `CD 02`, and so on. Various-artists releases
use `Compilations/Album (Year)/01 - Track Artist - Title.ext`.

The organizer preserves MP3, FLAC, and M4A codecs. It does not transcode audio.

## Install on macOS

Install Homebrew first, then run:

```sh
./setup_macos.sh
```

This installs beets, MusicBrainz/AcoustID fingerprinting support, MP3/FLAC/M4A
validation tools, and the Filetote plugin used to carry album artwork and other
sidecars. Rerun the setup script after a Homebrew beets upgrade if its isolated
Python environment loses optional plugins.

MusicBrainz Picard is optional but helpful for manually resolving unusual or
ambiguous releases:

```sh
brew install --cask musicbrainz-picard
```

## Preview one album

Preview is the default and does not write tags or move files:

```sh
./organize_music.sh \
  --library-root "/Volumes/external/Music/Downloaded" \
  --review-all \
  "/Volumes/external/Music/Downloaded/Wet Leg/Moisturizer (2025)"
```

The command checks the audio, searches MusicBrainz, asks you to approve the
match, and prints every proposed destination path. Preview state is temporary.

For a known release, constrain matching with its MusicBrainz release ID or URL:

```sh
./organize_music.sh \
  --library-root "/Volumes/external/Music/Downloaded" \
  --search-id 02f68162-bf45-4c0a-bc00-a0f84628a67a \
  "/Volumes/external/Music/Downloaded/Asking Alexandria - Where Do We Go From Here (2024)"
```

## Apply one album

After reviewing the preview, repeat with `--apply`:

```sh
./organize_music.sh \
  --library-root "/Volumes/external/Music/Downloaded" \
  --apply --review-all \
  "/Volumes/external/Music/Downloaded/Wet Leg/Moisturizer (2025)"
```

Apply mode writes accepted metadata and moves files in place. It also:

- carries CUE sheets, logs, artwork, checksums, PDFs, and playlists;
- reports corrupt files and duplicate albums without deleting duplicates;
- removes `.DS_Store`, AppleDouble `._*` files, and empty source directories;
- records its catalog, resume state, configuration, and logs under
  `<library-root>/.music-organizer/`.

Keep a backup until the resulting library has been reviewed.

## Process the whole library

Preview first:

```sh
./organize_music.sh \
  --library-root "/Volumes/external/Music/Downloaded" \
  "/Volumes/external/Music/Downloaded"
```

Then apply:

```sh
./organize_music.sh \
  --library-root "/Volumes/external/Music/Downloaded" \
  --apply \
  "/Volumes/external/Music/Downloaded"
```

High-confidence matches are accepted automatically. Ambiguous matches require
input and skipped releases are logged. Add `--review-all` to confirm every
album, including high-confidence matches.

You can set `MUSIC_LIBRARY_ROOT` instead of passing `--library-root` repeatedly:

```sh
export MUSIC_LIBRARY_ROOT="/Volumes/external/Music/Downloaded"
./organize_music.sh --review-all "$MUSIC_LIBRARY_ROOT/Wet Leg/Moisturizer (2025)"
```

