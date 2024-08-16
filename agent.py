#!/usr/bin/env python3

import os
import sys
import subprocess
import argparse
import os
from pathlib import Path
from openai import OpenAI

client = OpenAI()
import json


def split_flac_cue(folder_path):
    """Split single FLAC file with CUE into multiple tracks using flacue.py in a Docker container"""
    flac_files = list(folder_path.glob('*.flac'))
    cue_files = list(folder_path.glob('*.cue'))

    if len(flac_files) == 1 and len(cue_files) == 1:
        docker_cmd = [
            'docker', 'run',
            '-v', f"{folder_path}:/workdir",
            '-e', f"PUID={os.getuid()}",
            '-e', f"PGID={os.getgid()}",
            '-it', 'dockerflac',
            'bash', '-c',
            f"cd /workdir && flacue.py '{flac_files[0].name}' '{cue_files[0].name}'"
        ]
        subprocess.run(docker_cmd)
    return f"Split FLAC file with CUE in {folder_path}"

def convert_flac_to_mp3(folder_path):
    """Convert all FLAC files to MP3 using flac2mp3.sh in a Docker container"""
    docker_cmd = [
        'docker', 'run',
        '-v', f"{folder_path}:/workdir",
        '-e', f"PUID={os.getuid()}",
        '-e', f"PGID={os.getgid()}",
        '-it', 'dockerflac',
        'bash', '-c',
        "cd /workdir && find . -name '*.flac' -print0 | xargs -0 -n1 -P2 flac2mp3.sh"
    ]
    subprocess.run(docker_cmd)
    return f"Converted FLAC files to MP3 in {folder_path}"

def rename_tracks(folder_path):
    """Rename MP3 files to the format: {TRACK_NUMBER} - {TRACK_TITLE}.mp3"""
    folder_path = Path(folder_path)
    for mp3_file in folder_path.glob('*.mp3'):
        parts = mp3_file.stem.split(' - ', 1)
        if len(parts) == 2:
            track_num, title = parts
            new_name = f"{int(track_num):02d} - {title}.mp3"
            mp3_file.rename(folder_path / new_name)
    return f"Renamed tracks in {folder_path}"

def update_metadata(folder_path):
    """Update MP3 metadata using MusicBrainz Picard"""
    subprocess.run(['picard', str(folder_path)])
    return f"Updated metadata for files in {folder_path}"

def rename_album_folder(folder_path):
    """Rename the album folder to {ALBUM_NAME} - ({ALBUM_YEAR})"""
    folder_path = Path(folder_path)
    print(f"Album folder should be renamed to: ALBUM_NAME - (YEAR)")
    print(f"Current folder name: {folder_path.name}")
    return f"Suggested renaming for folder: {folder_path}"

def get_folder_contents(path):
    """Get the contents of the folder"""
    folder_path = Path(path)
    contents = list(folder_path.glob('*'))
    return f"Folder contents: {[str(item) for item in contents]}"

def process_album(folder_path):
    """Process an album folder according to the defined rules using OpenAI agent"""
    folder_path = Path(folder_path).resolve()

    if not folder_path.is_dir():
        print(f"Error: {folder_path} is not a valid directory")
        return

    functions = [
        {
            "name": "split_flac_cue",
            "description": "Split single FLAC file with CUE into multiple tracks",
            "parameters": {
                "type": "object",
                "properties": {
                    "folder_path": {"type": "string", "description": "Path to the folder containing FLAC and CUE files"}
                },
                "required": ["folder_path"]
            }
        },
        {
            "name": "convert_flac_to_mp3",
            "description": "Convert all FLAC files to MP3",
            "parameters": {
                "type": "object",
                "properties": {
                    "folder_path": {"type": "string", "description": "Path to the folder containing FLAC files"}
                },
                "required": ["folder_path"]
            }
        },
        {
            "name": "rename_tracks",
            "description": "Rename MP3 files to the format: {TRACK_NUMBER} - {TRACK_TITLE}.mp3",
            "parameters": {
                "type": "object",
                "properties": {
                    "folder_path": {"type": "string", "description": "Path to the folder containing MP3 files"}
                },
                "required": ["folder_path"]
            }
        },
        {
            "name": "update_metadata",
            "description": "Update MP3 metadata using MusicBrainz Picard",
            "parameters": {
                "type": "object",
                "properties": {
                    "folder_path": {"type": "string", "description": "Path to the folder containing MP3 files"}
                },
                "required": ["folder_path"]
            }
        },
        {
            "name": "rename_album_folder",
            "description": "Suggest renaming the album folder to {ALBUM_NAME} - ({ALBUM_YEAR})",
            "parameters": {
                "type": "object",
                "properties": {
                    "folder_path": {"type": "string", "description": "Path to the album folder"}
                },
                "required": ["folder_path"]
            }
        },
        {
            "name": "get_folder_contents",
            "description": "Get the contents of the folder",
            "parameters": {
                "type": "object",
                "properties": {
                    "folder_path": {"type": "string", "description": "Path to the folder"}
                },
                "required": ["folder_path"]
            }
        }
    ]

    messages = [
        {"role": "system", "content": "You are an AI assistant that helps process music albums. Your task is to organize and process the music files in a given folder according to these specific rules:\n\n1. Single FLAC file + CUE file should be split into track files, using the `flacue.py` tool\n2. All FLAC files should be converted to MP3, using the `flac2mp3.sh` script\n3. All individual track files should be renamed to `{TRACK_NUMBER} - {TRACK_TITLE}.mp3`. Track numbers should be 2 digits and have leading `0` (e.g., `01 - Song Title.mp3`)\n4. MP3 metadata should be updated using `picard`\n5. Album folder names should follow this convention: `{ALBUM_NAME} - ({ALBUM_YEAR})`\n\nApply these rules in the correct order to process the album folder."},
        {"role": "user", "content": f"Process the album in the folder: {folder_path}. Start by checking the folder contents and then apply the necessary operations in the correct order."}
    ]

    while True:
        response = client.chat.completions.create(model="gpt-4o",
        messages=messages,
        functions=functions,
        function_call="auto")

        message = response.choices[0].message

        if message.function_call:
            function_name = message.function_call.name
            function_args = json.loads(message.function_call.arguments)

            function_response = globals()[function_name](**function_args)

            messages.append({
                "role": "function",
                "name": function_name,
                "content": function_response
            })
        else:
            print(message.content)
            break

    print("Album processing completed.")

def main():
    parser = argparse.ArgumentParser(description="Process a music album folder")
    parser.add_argument("folder_path", help="Path to the album folder")
    args = parser.parse_args()

    process_album(args.folder_path)

if __name__ == "__main__":
    main()
