#!/usr/bin/env python3

import argparse
import os
from datetime import datetime
from cloudbackup import RemoteStorage


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
    parser.add_argument('-p', '--path',
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
    filename = args.filename
    if args.filename is None:
        filename = args.path
    RemoteStorage.upload(storage='gdrive', path='/home/ddqof/Videos/cons.mkv')


if __name__ == '__main__':
    main()
