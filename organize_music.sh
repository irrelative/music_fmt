#!/bin/bash

set -euo pipefail

PROGRAM_NAME=${0##*/}

APPLY=0
REVIEW_ALL=0
SEARCH_ID=""
LIBRARY_ROOT_ARG=${MUSIC_LIBRARY_ROOT:-}
TARGET_ARG=""
TEMP_STATE=""

usage() {
    cat <<EOF
Usage:
  $PROGRAM_NAME --library-root ROOT [--review-all] [--search-id ID] TARGET
  $PROGRAM_NAME --library-root ROOT --apply [--review-all] [--search-id ID] TARGET

Preview is the default. It identifies music and prints the paths beets would
use, but does not write tags or move files. Use --apply to write accepted
metadata and organize files beneath ROOT. MUSIC_LIBRARY_ROOT may be used instead
of --library-root.

Options:
  --apply                 Write tags and move files into canonical paths.
  --library-root ROOT     Canonical destination root containing TARGET.
  --review-all            Confirm every MusicBrainz match, including strong ones.
  --search-id ID          Restrict a single-album lookup to a MusicBrainz ID/URL.
  -h, --help              Show this help.

Examples:
  $PROGRAM_NAME --library-root /Volumes/Music /Volumes/Music/Wet\ Leg
  $PROGRAM_NAME --library-root /Volumes/Music --apply --review-all /Volumes/Music/Wet\ Leg
  $PROGRAM_NAME --library-root /Volumes/Music /Volumes/Music
  $PROGRAM_NAME --library-root /Volumes/Music --apply /Volumes/Music
EOF
}

die() {
    printf 'Error: %s\n' "$*" >&2
    exit 1
}

cleanup_temp() {
    if [[ -n "$TEMP_STATE" && -d "$TEMP_STATE" ]]; then
        rm -rf -- "$TEMP_STATE"
    fi
}

trap cleanup_temp EXIT
trap 'exit 130' INT
trap 'exit 143' TERM

while (($#)); do
    case $1 in
        --apply)
            APPLY=1
            ;;
        --review-all)
            REVIEW_ALL=1
            ;;
        --library-root)
            shift
            (($#)) || die "--library-root requires a directory"
            LIBRARY_ROOT_ARG=$1
            ;;
        --search-id)
            shift
            (($#)) || die "--search-id requires an ID or URL"
            SEARCH_ID=$1
            ;;
        -h|--help)
            usage
            exit 0
            ;;
        --)
            shift
            (($#)) || die "TARGET is required"
            [[ -z "$TARGET_ARG" ]] || die "only one TARGET may be specified"
            TARGET_ARG=$1
            shift
            (($# == 0)) || die "only one TARGET may be specified"
            break
            ;;
        -*)
            die "unknown option: $1"
            ;;
        *)
            [[ -z "$TARGET_ARG" ]] || die "only one TARGET may be specified"
            TARGET_ARG=$1
            ;;
    esac
    shift
done

[[ -n "$TARGET_ARG" ]] || die "TARGET is required (try --help)"
[[ -n "$LIBRARY_ROOT_ARG" ]] ||
    die "--library-root ROOT is required (or set MUSIC_LIBRARY_ROOT)"
[[ -d "$LIBRARY_ROOT_ARG" ]] ||
    die "library root does not exist: $LIBRARY_ROOT_ARG"
[[ -d "$TARGET_ARG" ]] || die "target directory does not exist: $TARGET_ARG"

LIBRARY_ROOT=$(realpath "$LIBRARY_ROOT_ARG")
TARGET=$(realpath "$TARGET_ARG")
case "$TARGET/" in
    "$LIBRARY_ROOT/"|"$LIBRARY_ROOT/"*) ;;
    *) die "target must be inside the library root: $LIBRARY_ROOT" ;;
esac

case "$TARGET/" in
    "$LIBRARY_ROOT/.music-organizer/"*)
        die "the organizer state directory cannot be imported"
        ;;
esac

for command_name in beet fpcalc ffprobe flac mp3val realpath; do
    command -v "$command_name" >/dev/null 2>&1 ||
        die "required command is not installed: $command_name"
done

BEET_BIN=$(command -v beet)
BEET_PYTHON=$(sed -n '1s/^#!//p' "$BEET_BIN")
[[ -x "$BEET_PYTHON" ]] || die "could not determine the Python used by beet"

"$BEET_PYTHON" -c 'import acoustid, beetsplug.chroma' >/dev/null 2>&1 ||
    die "pyacoustid/chroma is unavailable in the beets environment"
"$BEET_PYTHON" -c 'import beetsplug.filetote' >/dev/null 2>&1 ||
    die "beets-filetote is unavailable in the beets environment"

if ! find "$TARGET" -type f \( \
    -iname '*.mp3' -o -iname '*.flac' -o -iname '*.m4a' \
    \) -print -quit | grep -q .; then
    die "target contains no MP3, FLAC, or M4A files"
fi

yaml_quote() {
    local value=$1
    value=${value//\'/\'\'}
    printf "'%s'" "$value"
}

write_config() {
    local config_path=$1
    local database_path=$2
    local state_path=$3
    local log_path=$4
    local write_value=$5
    local move_value=$6
    local incremental_value=$7

    {
        printf 'directory: %s\n' "$(yaml_quote "$LIBRARY_ROOT")"
        printf 'library: %s\n' "$(yaml_quote "$database_path")"
        printf 'statefile: %s\n' "$(yaml_quote "$state_path")"
        cat <<'YAML'

plugins:
  - musicbrainz
  - chroma
  - fromfilename
  - badfiles
  - duplicates
  - filetote

ignore_hidden: yes
ignore:
  - '.*'
  - '*~'
  - 'System Volume Information'
  - 'lost+found'
clutter:
  - 'Thumbs.DB'
  - '.DS_Store'

import:
YAML
        printf '  write: %s\n' "$write_value"
        printf '  move: %s\n' "$move_value"
        printf '  incremental: %s\n' "$incremental_value"
        printf '  log: %s\n' "$(yaml_quote "$log_path")"
        cat <<'YAML'
  copy: no
  autotag: yes
  resume: ask
  duplicate_action: ask
  duplicate_verbose_prompt: yes
  none_rec_action: ask
  quiet_fallback: skip
  detail: yes

original_date: yes
per_disc_numbering: yes
asciify_paths: no
art_filename: cover

paths:
  'comp:true disctotal:2..': 'Compilations/$album%if{$year, ($year), (Unknown Year)}%aunique{}/CD $disc/$track - $artist - $title'
  comp: 'Compilations/$album%if{$year, ($year), (Unknown Year)}%aunique{}/$track - $artist - $title'
  'disctotal:2..': '$albumartist/$album%if{$year, ($year), (Unknown Year)}%aunique{}/CD $disc/$track - $title'
  default: '$albumartist/$album%if{$year, ($year), (Unknown Year)}%aunique{}/$track - $title'
  singleton: '$artist/Non-Album Tracks/$title'

chroma:
  auto: yes

badfiles:
  check_on_import: yes
  import_action_on_error: skip
  import_action_on_warning: ask
  commands:
    m4a: 'ffprobe -v error'

filetote:
  extensions: '.cue .log .pdf .m3u .m3u8 .jpg .jpeg .png .txt .nfo .md5 .ffp .sfv .accurip'
  print_ignored: yes
  duplicate_action: merge
  paths:
    'filetote:default': '$albumpath/$subpath$old_filename'
  exclude:
    filenames: '.DS_Store'
    patterns:
      apple_double:
        - '._*'
        - '**/._*'
YAML
    } >"$config_path"
}

run_beet() {
    BEETSDIR=$STATE_DIR "$BEET_BIN" --config "$CONFIG_PATH" "$@"
}

IMPORT_ARGS=(import)
((REVIEW_ALL == 0)) || IMPORT_ARGS+=('--timid')
[[ -z "$SEARCH_ID" ]] || IMPORT_ARGS+=('--search-id' "$SEARCH_ID")

if ((APPLY)); then
    STATE_DIR="$LIBRARY_ROOT/.music-organizer"
    mkdir -p -- "$STATE_DIR/logs"

    RUN_STAMP=$(date '+%Y%m%d-%H%M%S')
    CONFIG_PATH="$STATE_DIR/config.yaml"
    DATABASE_PATH="$STATE_DIR/library.db"
    STATE_PATH="$STATE_DIR/import-state.pickle"
    LOG_PATH="$STATE_DIR/logs/import-$RUN_STAMP.log"

    write_config "$CONFIG_PATH" "$DATABASE_PATH" "$STATE_PATH" "$LOG_PATH" yes yes yes

    printf 'Applying MusicBrainz metadata and organizing:\n  %s\n\n' "$TARGET"
    printf 'Run log:\n  %s\n\n' "$LOG_PATH"

    set +e
    run_beet "${IMPORT_ARGS[@]}" --move --write --incremental "$TARGET"
    IMPORT_STATUS=$?
    set -e

    if ((IMPORT_STATUS != 0)); then
        printf '\nImport failed or was interrupted (exit %d). No cleanup was run.\n' \
            "$IMPORT_STATUS" >&2
        exit "$IMPORT_STATUS"
    fi

    printf '\nDuplicate album report (report only):\n'
    run_beet duplicates --album --path || true

    if [[ -d "$TARGET" ]]; then
        printf '\nRemoving known platform junk:\n'
        find "$TARGET" -type f \( -name '.DS_Store' -o -name '._*' \) \
            -print -delete

        printf '\nRemoving empty source directories:\n'
        find "$TARGET" -depth -mindepth 1 -type d -empty -print -delete
    fi

    if [[ "$TARGET" != "$LIBRARY_ROOT" && -d "$TARGET" ]]; then
        rmdir "$TARGET" 2>/dev/null || true
    fi

    if [[ -d "$TARGET" ]]; then
        printf '\nFiles left for manual review:\n'
        find "$TARGET" \
            -path "$LIBRARY_ROOT/.music-organizer" -prune -o \
            -type f \
            ! -iname '*.mp3' ! -iname '*.flac' ! -iname '*.m4a' \
            ! -iname '*.cue' ! -iname '*.log' ! -iname '*.pdf' \
            ! -iname '*.m3u' ! -iname '*.m3u8' \
            ! -iname '*.jpg' ! -iname '*.jpeg' ! -iname '*.png' \
            ! -iname '*.txt' ! -iname '*.nfo' ! -iname '*.md5' \
            ! -iname '*.ffp' ! -iname '*.sfv' ! -iname '*.accurip' \
            ! -name "$PROGRAM_NAME" -print
    fi

    printf '\nApply completed. Review skipped or unmatched releases in:\n  %s\n' \
        "$LOG_PATH"
else
    TEMP_STATE=$(mktemp -d "${TMPDIR:-/tmp}/music-organizer-preview.XXXXXX")
    STATE_DIR=$TEMP_STATE
    CONFIG_PATH="$STATE_DIR/config.yaml"
    DATABASE_PATH="$STATE_DIR/library.db"
    STATE_PATH="$STATE_DIR/import-state.pickle"
    LOG_PATH="$STATE_DIR/import.log"

    write_config "$CONFIG_PATH" "$DATABASE_PATH" "$STATE_PATH" "$LOG_PATH" no no no

    printf 'Preview only; tags and files will not be changed:\n  %s\n\n' "$TARGET"

    set +e
    run_beet "${IMPORT_ARGS[@]}" --nocopy --nomove --nowrite \
        --noresume --noincremental "$TARGET"
    IMPORT_STATUS=$?
    set -e

    if ((IMPORT_STATUS != 0)); then
        printf '\nPreview failed or was interrupted (exit %d).\n' "$IMPORT_STATUS" >&2
        exit "$IMPORT_STATUS"
    fi

    printf '\nProposed audio path changes:\n'
    if ! run_beet move --pretend; then
        printf 'No accepted albums are available to preview.\n'
    fi

    if [[ -s "$LOG_PATH" ]]; then
        printf '\nSkipped or unmatched releases:\n'
        cat "$LOG_PATH"
    fi

    printf '\nPreview completed; no tags or files were changed.\n'
    printf 'Repeat with --apply to perform these operations.\n'
fi
