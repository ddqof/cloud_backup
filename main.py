#!/usr/bin/env python3

import argparse
from colorama import init, Fore, Style
from cloudbackup.gdrive import GDrive
import re


def parse_args():
    parser = argparse.ArgumentParser(
        usage="[-s] STORAGE_NAME",
        prog="main.py",
        description="""Tool for backing your data up on
        Google Drive.\nUse commands the following commands:\n
        `ls` for list all files,\n
        `dl filename [path]` for download file called filename to path (if not specified then upload to pwd,\n
        `rm filename` to delete file called filename. Be careful! It deletes without ability to restore,\n
        `exit` to exit.""",
        epilog="""Author: Dmitry Podaruev <ddqof.vvv@gmail.com>"""
    )
    parser.add_argument("-s", "--storage",
                        metavar="",
                        help="specify remote storage name "
                             "(examples: gdrive, yadisk)",
                        type=str)
    return parser.parse_args()


def cli_handler():
    gdrive = GDrive()
    while True:
        args = re.search(r"(\w{1,3}) ?(.*)", input())
        command = args.group(1)
        key = args.group(2)
        if command == "ls":
            files = gdrive.list_files()
            for filename in files:
                if files[filename] == "application/vnd.google-apps.folder":
                    print(Fore.CYAN + filename + Style.RESET_ALL)
                else:
                    print(filename)
        elif command == "dl":
            if len(args.groups()) == 2:
                print(gdrive.download(filename=key))
            else:
                file = key.split()[0]
                path = key.split()[1]
                print(gdrive.download(filename=file, path=path))
        elif command == "ul":
            print(gdrive.upload(file_abs_path=key))
        elif command == "rm":
            print(gdrive.delete(filename=key))
        elif command == "cd":
            try:
                print(gdrive.change_directory(directory=gdrive.directories_history[-2] if key == ".." else key))
            except IndexError:
                print("Switched to root")
        elif command == "pwd":
            print(gdrive.current_directory)
        elif command == "exit":
            return
        else:
            print("Wrong command")


def main():
    init()
    cli_handler()


if __name__ == "__main__":
    main()
