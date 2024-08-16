#!/usr/bin/env python3

import os
import sys
import subprocess
import argparse
import logging
from pathlib import Path
from openai import OpenAI

client = OpenAI()
import json
from mutagen.mp3 import MP3
from mutagen.easyid3 import EasyID3

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def split_flac_cue(folder_path):
    """Split single FLAC file with CUE into multiple tracks using flacue.py in a Docker container"""
    logger.info(f"Splitting FLAC file with CUE in {folder_path}")
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
        logger.info(f"Running command: {' '.join(docker_cmd)}")
        subprocess.run(docker_cmd)
        logger.info("FLAC file split completed")
    else:
        logger.warning("No single FLAC + CUE pair found, skipping split operation")
    return f"Split FLAC file with CUE in {folder_path}"

def convert_flac_to_mp3(folder_path):
    """Convert all FLAC files to MP3 using flac2mp3.sh in a Docker container"""
    logger.info(f"Converting FLAC files to MP3 in {folder_path}")
    docker_cmd = [
        'docker', 'run',
        '-v', f"{folder_path}:/workdir",
        '-e', f"PUID={os.getuid()}",
        '-e', f"PGID={os.getgid()}",
        '-it', 'dockerflac',
        'bash', '-c',
        "cd /workdir && find . -name '*.flac' -print0 | xargs -0 -n1 -P2 flac2mp3.sh"
    ]
    logger.info(f"Running command: {' '.join(docker_cmd)}")
    subprocess.run(docker_cmd)
    logger.info("FLAC to MP3 conversion completed")
    return f"Converted FLAC files to MP3 in {folder_path}"

def rename_tracks(folder_path):
    """Rename MP3 files to the format: {TRACK_NUMBER} - {TRACK_TITLE}.mp3 using metadata"""
    logger.info(f"Renaming tracks in {folder_path}")
    folder_path = Path(folder_path)
    for mp3_file in folder_path.glob('*.mp3'):
        try:
            audio = EasyID3(mp3_file)
            track_num = audio.get('tracknumber', [''])[0].split('/')[0].zfill(2)
            title = audio.get('title', [''])[0]
            if track_num and title:
                new_name = f"{track_num} - {title}.mp3"
                new_path = folder_path / new_name
                mp3_file.rename(new_path)
                logger.info(f"Renamed: {mp3_file.name} -> {new_name}")
            else:
                logger.warning(f"Skipped renaming {mp3_file.name}: Missing track number or title in metadata")
        except Exception as e:
            logger.error(f"Error renaming {mp3_file.name}: {str(e)}")
    logger.info("Track renaming completed")
    return f"Renamed tracks in {folder_path}"

def update_metadata(path):
    """Update MP3 metadata using beets"""
    logger.info(f"Updating metadata for files in {path}")
    beets_cmd = [
        'beet', 'import', '-A', '--write', '-q', str(path)
    ]
    try:
        subprocess.run(beets_cmd, check=True, capture_output=True, text=True)
        logger.info("Metadata update completed")
        return f"Updated metadata for files in {path}"
    except subprocess.CalledProcessError as e:
        logger.error(f"Error updating metadata: {e.stderr}")
        return f"Failed to update metadata for files in {path}: {e.stderr}"

def rename_album_folder(folder_path):
    """Rename the album folder to {ALBUM_NAME} - ({ALBUM_YEAR})"""
    logger.info(f"Suggesting rename for album folder: {folder_path}")
    folder_path = Path(folder_path)
    logger.info(f"Album folder should be renamed to: ALBUM_NAME - (YEAR)")
    logger.info(f"Current folder name: {folder_path.name}")
    return f"Suggested renaming for folder: {folder_path}"

def get_folder_contents(folder_path):
    """Get the contents of the folder"""
    logger.info(f"Getting contents of folder: {folder_path}")
    folder_path = Path(folder_path)
    contents = list(folder_path.glob('*'))
    logger.info(f"Folder contents: {[str(item) for item in contents]}")
    return f"Folder contents: {[str(item) for item in contents]}"

def delete_file(file_path):
    """Delete a file"""
    logger.info(f"Deleting file: {file_path}")
    file_path = Path(file_path)
    if file_path.is_file():
        file_path.unlink()
        logger.info(f"Deleted file: {file_path}")
        return f"Deleted file: {file_path}"
    else:
        logger.warning(f"File not found: {file_path}")
        return f"File not found: {file_path}"

def rename_folder(old_path, new_name):
    """Rename a folder"""
    logger.info(f"Renaming folder: {old_path} to {new_name}")
    old_path = Path(old_path)
    new_path = old_path.parent / new_name
    if old_path.is_dir():
        old_path.rename(new_path)
        logger.info(f"Renamed folder: {old_path} to {new_path}")
        return f"Renamed folder: {old_path} to {new_path}"
    else:
        logger.warning(f"Folder not found: {old_path}")
        return f"Folder not found: {old_path}"

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
            "description": "Update MP3 metadata using beets",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Path to the folder containing MP3 files"}
                },
                "required": ["path"]
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
        },
        {
            "name": "delete_file",
            "description": "Delete a file",
            "parameters": {
                "type": "object",
                "properties": {
                    "file_path": {"type": "string", "description": "Path to the file to be deleted"}
                },
                "required": ["file_path"]
            }
        },
        {
            "name": "rename_folder",
            "description": "Rename a folder",
            "parameters": {
                "type": "object",
                "properties": {
                    "old_path": {"type": "string", "description": "Path to the folder to be renamed"},
                    "new_name": {"type": "string", "description": "New name for the folder"}
                },
                "required": ["old_path", "new_name"]
            }
        }
    ]

    messages = [
        {"role": "system", "content": "You are an AI assistant that helps process music albums. Your task is to organize and process the music files in a given folder according to these specific rules:\n\n1. Single FLAC file + CUE file should be split into track files, using the `flacue.py` tool\n2. All FLAC files should be converted to MP3, using the `flac2mp3.sh` script\n3. MP3 metadata should be updated using `picard`\n4. All individual track files should be renamed to `{TRACK_NUMBER} - {TRACK_TITLE}.mp3` using the metadata. Track numbers should be 2 digits and have leading `0` (e.g., `01 - Song Title.mp3`)\n5. Album folder names should follow this convention: `{ALBUM_NAME} - ({ALBUM_YEAR})`. Use the rename_folder function to implement this.\n6. After processing, delete all FLAC files and other non-MP3 files (e.g., CUE, LOG) in the folder\n\nApply these rules in the correct order to process the album folder."},
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
            # Remove 'functions::' prefix if present
            function_name = function_name.split('::')[-1]
            function_args = json.loads(message.function_call.arguments)

            logger.info(f"Calling function: {function_name} with args: {function_args}")
            function_response = globals()[function_name](**function_args)
            logger.info(f"Function response: {function_response}")

            messages.append({
                "role": "function",
                "name": function_name,
                "content": function_response
            })
        else:
            logger.info(f"AI response: {message.content}")
            break

    logger.info("Album processing completed.")

def main():
    parser = argparse.ArgumentParser(description="Process a music album folder")
    parser.add_argument("folder_path", help="Path to the album folder")
    args = parser.parse_args()

    process_album(args.folder_path)

if __name__ == "__main__":
    main()
