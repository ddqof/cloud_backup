#!/usr/bin/env python3

import argparse
import os
from datetime import datetime
from cloudbackup import RemoteStorage
from cloudbackup import file_operations


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
                        help='specify remote storage name '
                             '(examples: gdrive, yadisk)',
                        type=str)
    parser.add_argument('-d', '--dir',
                        metavar='',
                        help='specify directory that you want to back up',
                        type=str)
    parser.add_argument('-f', '--filename',
                        metavar='',
                        help='specify backup name '
                             '(default: same as the directory)',
                        type=str)
    parser.add_argument('-z', '--zip',
                        help='compress your data using zip',
                        action='store_true')
    return parser.parse_args()


def main():
    args = parse_args()
    timestamp = str(datetime.now()).split('.')[0]

    if args.storage:
        if os.path.isfile(args.dir):  # check if args.dir is a file
            file_size = os.path.getsize(args.dir)
        elif os.path.isdir(args.dir):  # check if args.dir is a directory
            file_size = file_operations.get_directory_size(args.dir)
        else:
            file_size = None

        filename = args.filename
        if args.filename is None:
            filename = args.dir

        if args.zip:
            file_operations.zip_directory(args.dir, filename)
            filename = filename + '.zip'

        RemoteStorage.upload(filename, timestamp, args.storage)  # TODO: try upload
        print(RemoteStorage.gdrive_token)

        if os.path.exists(filename):
            os.remove(filename)

# def ideal_main():
#     args = parse_args()
#     filename = args.filename
#     if args.filename is None:
#         filename = args.dir
#     try:
#         RemoteStorage.upload(storage=args.storage, filename=filename)


if __name__ == '__main__':
    main()
