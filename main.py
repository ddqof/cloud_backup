#!/usr/bin/env python3

import argparse
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
    return parser.parse_args()


def main():
    args = parse_args()
    RemoteStorage.upload(storage='gdrive', file_abs_path='/home/ddqof/uni/ma/all_conspects', multipart=True)


if __name__ == '__main__':
    main()
