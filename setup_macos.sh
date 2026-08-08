#!/bin/bash

set -euo pipefail

command -v brew >/dev/null 2>&1 || {
    printf 'Error: Homebrew is required: https://brew.sh\n' >&2
    exit 1
}

brew install beets chromaprint mp3val ffmpeg flac

BEET_BIN=$(command -v beet)
BEET_PYTHON=$(sed -n '1s/^#!//p' "$BEET_BIN")

if [[ ! -x "$BEET_PYTHON" ]]; then
    printf 'Error: could not determine the Python used by beet\n' >&2
    exit 1
fi

"$BEET_PYTHON" -m pip install --upgrade pyacoustid beets-filetote

printf '\nInstalled music_fmt dependencies:\n'
beet version
fpcalc -version
mp3val -v 2>&1 | sed -n '1p'
"$BEET_PYTHON" -c \
    'import acoustid, beetsplug.filetote; print("AcoustID and Filetote: OK")'
