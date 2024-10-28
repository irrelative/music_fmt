#!/usr/bin/env python3

import os
import subprocess
import argparse


def get_files(f_names, ext):
    return [f for f in f_names if f.endswith(ext)]


def main(flac_file, cue_file):
    root = os.path.dirname(flac_file)
    print(f'\nConverting: {root}')
    cmd_args = ['shnsplit', '-f', cue_file, '-t', '%n - %t', '-o', 'flac', flac_file]
    print(' '.join(cmd_args))
    try:
        ret = subprocess.run(cmd_args, cwd=root, check=True, capture_output=True)
    except Exception as ex:
        print(f'Error: {root}')
        print(ex)
    else:
        print(f'Converted {root}')
        os.remove(flac_file)
        os.remove(cue_file)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Split FLAC file using CUE sheet')
    parser.add_argument('flac_file', help='Path to the FLAC file')
    parser.add_argument('cue_file', help='Path to the CUE file')
    args = parser.parse_args()

    main(args.flac_file, args.cue_file)
