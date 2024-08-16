#!/usr/bin/env python3

import os
import subprocess


def get_files(f_names, ext):
    return [f for f in f_names if f.endswith(ext)]


def main():
    # If there is 1 cue file and 1 flac file in a folder, consider it convertable
    for root, d_names,f_names in os.walk('.'):
        cue_files = get_files(f_names, '.cue')
        flac_files = get_files(f_names, '.flac')
        if len(cue_files) == 1 and len(flac_files) == 1:
            print(f'\nConverting: {root}')
            cmd_args = ['shnsplit', '-f', cue_files[0], '-t', '%n - %t', '-o', 'flac', flac_files[0]]
            print(' '.join(cmd_args))
            try:
                ret = subprocess.run(cmd_args, cwd=root, check=True, capture_output=True)
            except Exception as ex:
                print(f'Error: {root}')
                print(ex)
            else:
                print(f'Converted {root}')
                os.remove(os.path.join(root, flac_files[0]))
                os.remove(os.path.join(root, cue_files[0]))


if __name__ == '__main__':
    main()
