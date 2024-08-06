#!/usr/bin/env python3

import os
import sys
import subprocess
import argparse
from pathlib import Path

def split_flac_cue(folder_path):
    """Split single FLAC file with CUE into multiple tracks using flacue.py"""
    flac_files = list(folder_path.glob('*.flac'))
    cue_files = list(folder_path.glob('*.cue'))
    
    if len(flac_files) == 1 and len(cue_files) == 1:
        subprocess.run(['python', 'flacue.py', str(flac_files[0]), str(cue_files[0])])

def convert_flac_to_mp3(folder_path):
    """Convert all FLAC files to MP3 using flac2mp3.sh"""
    subprocess.run(['bash', 'flac2mp3.sh', str(folder_path)])

def rename_tracks(folder_path):
    """Rename MP3 files to the format: {TRACK_NUMBER} - {TRACK_TITLE}.mp3"""
    for mp3_file in folder_path.glob('*.mp3'):
        # This is a placeholder. In a real scenario, we'd use a library like mutagen
        # to read the track number and title from the MP3 metadata.
        # For now, we'll assume the files are already named correctly and just ensure
        # the track number has a leading zero if needed.
        parts = mp3_file.stem.split(' - ', 1)
        if len(parts) == 2:
            track_num, title = parts
            new_name = f"{int(track_num):02d} - {title}.mp3"
            mp3_file.rename(folder_path / new_name)

def update_metadata(folder_path):
    """Update MP3 metadata using MusicBrainz Picard"""
    # Note: This is a simplified version. Picard typically has a GUI,
    # so automating it might require additional setup or a different tool.
    subprocess.run(['picard', str(folder_path)])

def rename_album_folder(folder_path):
    """Rename the album folder to {ALBUM_NAME} - ({ALBUM_YEAR})"""
    # This is a placeholder. In a real scenario, we'd extract this info
    # from the audio files' metadata or from an external source.
    # For now, we'll just print a message.
    print(f"Album folder should be renamed to: ALBUM_NAME - (YEAR)")
    print(f"Current folder name: {folder_path.name}")

def process_album(folder_path):
    """Process an album folder according to the defined rules"""
    folder_path = Path(folder_path).resolve()
    
    if not folder_path.is_dir():
        print(f"Error: {folder_path} is not a valid directory")
        return

    split_flac_cue(folder_path)
    convert_flac_to_mp3(folder_path)
    rename_tracks(folder_path)
    update_metadata(folder_path)
    rename_album_folder(folder_path)

def main():
    parser = argparse.ArgumentParser(description="Process a music album folder")
    parser.add_argument("folder_path", help="Path to the album folder")
    args = parser.parse_args()

    process_album(args.folder_path)

if __name__ == "__main__":
    main()
