#!/usr/bin/env python3

import argparse
import zipfile
import os
from datetime import datetime
from storage import RemoteStorage


def get_directory_size(start_path='.'):
    total_size = 0
    for dirpath, dirnames, filenames in os.walk(start_path):
        for f in filenames:
            fp = os.path.join(dirpath, f)
            # skip if it is symbolic link
            if not os.path.islink(fp):
                total_size += os.path.getsize(fp)

    return total_size


def zip_directory(directory, zip_name):
    with zipfile.ZipFile(zip_name + '.zip', 'w') as zf:
        for root, dirs, files in os.walk(directory):
            for file in files:
                zf.write(os.path.join(root, file))


def parse_args():
    parser = argparse.ArgumentParser(
        usage='[-s] STORAGE_NAME [-d] DIRECTORY [-n] BACKUP_NAME [-z]',
        prog='main.py',
        description='''Tool for backing your data up on
        Google Drive and Yandex.Disk.''',
        epilog='''Author: Dmitry Podaruev <ddqof.vvv@gmail.com>'''
    )
    parser.add_argument('-s', '--storage',
                        metavar='',
                        help='specify remote storage name'
                             '(examples: gdrive, yadisk)',
                        type=str)
    parser.add_argument('-d', '--dir',
                        metavar='',
                        help='specify directory that you want to back up',
                        type=str)
    parser.add_argument('-f', '--filename',
                        metavar='',
                        help='specify backup name'
                             '(default: same as the directory)',
                        type=str)
    parser.add_argument('-z', '--zip',
                        help='compress your data using zip',
                        action='store_true')
    return parser.parse_args()


def main():
    args = parse_args()
    storage = RemoteStorage()
    timestamp = str(datetime.now()).split('.')[0]

    if args.storage:
        if os.path.isfile(args.dir):  # check if args.dir is a file
            file_size = os.path.getsize(args.dir)
        elif os.path.isdir(args.dir):  # check if args.dir is a directory
            file_size = get_directory_size(args.dir)
        else:
            file_size = None

        filename = args.filename
        if args.filename is None:
            filename = args.dir

        if args.zip:
            zip_directory(args.dir, filename)
            filename = filename + '.zip'

        # storage.upload(filename, file_size, timestamp, args.storage)  #TODO: try upload

        if os.path.exists(filename):
            os.remove(filename)


if __name__ == '__main__':
    main()
