#!/usr/bin/env python3

import argparse
from cloudbackup import RemoteStorage
from colorama import init, Fore, Back, Style


def parse_args():
    parser = argparse.ArgumentParser(
        usage="[-s] STORAGE_NAME [-d] DIRECTORY [-n] BACKUP_NAME [-z]",
        prog="main.py",
        description="""Tool for backing your data up on
        Google Drive and Yandex.Disk.""",
        epilog="""Author: Dmitry Podaruev <ddqof.vvv@gmail.com>"""
    )
    parser.add_argument("-s", "--storage",
                        metavar="",
                        help="specify remote storage name "
                             "(examples: gdrive, yadisk)",
                        type=str)
    return parser.parse_args()


def cli_handler():
    while True:
        commands = input()
        args = commands.split()
        if args[0] == "ls":
            list_files()
        elif args[0] == "dl":
            if len(args) == 2:
                print(RemoteStorage.download(filename=args[1]))
            else:
                print(RemoteStorage.download(filename=args[1], path=args[2]))
        elif args[0] == "ul":
            print(RemoteStorage.upload(args[1]))
        elif args[0] == "rm":
            print(RemoteStorage.delete(args[1]))
        elif args[0] == "exit":
            return

    pass


def list_files():
    files = RemoteStorage.list_files()
    for name in files:
        if files[name] == "application/vnd.google-apps.folder":
            print(Fore.CYAN + name + Style.RESET_ALL)
        else:
            print(name)


def main():
    init()
    cli_handler()
    args = parse_args()


if __name__ == "__main__":
    main()
