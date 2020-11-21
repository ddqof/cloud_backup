#!/usr/bin/env python3

import os
from colorama import init, Fore, Style
from cloudbackup.gdrive import GDrive
from cloudbackup.yadisk import YaDisk
from cloudbackup.exceptions import RemoteFileNotFoundException
from defaults import (GDRIVE_SORT_KEYS, YADISK_SORT_KEYS,
                       CONFIRM_CHOICE_STRING, ABORTED_MSG)
from cloudbackup._file_objects import GDriveFile
from parser import parse_args


def handle_gdrive(args):
    gdrive = GDrive()
    try:
        file = gdrive.get_file_object_by_id(args.id)
        file_id = file.id
    except RemoteFileNotFoundException:
        file_id = None
    if args.list:
        if args.all:
            files = []
            pages = gdrive.lsdir(dir_id=file_id, owners=['me'], page_size=1000,
                                 order_by=GDRIVE_SORT_KEYS[args.order_by])
            for page in pages:
                files.extend(page)
            for file in files:
                print_gdrive_file(file)
        else:
            pages = gdrive.lsdir(dir_id=file_id, owners=['me'], page_size=20, order_by=GDRIVE_SORT_KEYS[args.order_by])
            for page in pages:
                for file in page:
                    print_gdrive_file(file)
                user_confirm = input(f"List next page? {CONFIRM_CHOICE_STRING}")
                if user_confirm in {"y", "yes", ""}:
                    continue
                else:
                    print(ABORTED_MSG)
                    break
    if args.download:
        try:
            print(gdrive.download(file, path=args.directory))
        except UnboundLocalError:
            print("Please specify ")
    if args.upload:
        print(gdrive.upload(args.directory))
    if args.remove:
        if args.permanently:
            user_confirm = input(f"Are you sure you want to delete {file.name} file? {CONFIRM_CHOICE_STRING}")
            if user_confirm in {"y", "yes", ""}:
                print(gdrive.remove(file_id=file.id, permanently=True))
            else:
                print(ABORTED_MSG)
        else:
            user_confirm = input(f"Are you sure you want to move {file.name} to trash? {CONFIRM_CHOICE_STRING}")
            if user_confirm in {"y", "yes", ""}:
                print(gdrive.remove(file_id=file.id))
            else:
                print(ABORTED_MSG)


def handle_yadisk(args):
    yadisk = YaDisk()
    if args.list:
        path = args.id
        if args.id == "root":
            path = "/"
        if path is None:
            files = yadisk.list_files(limit=1000, sort=YADISK_SORT_KEYS[args.order_by])
            for file in files:
                print_yadisk_file(file)
        else:
            pages = yadisk.lsdir(path, sort=YADISK_SORT_KEYS[args.order_by])
            for page in pages:
                current_page_number = pages.index(page) + 1
                print(f"Page {current_page_number} of {len(pages)}")
                for file in page:
                    print_yadisk_file(file)
                user_confirm = input(f"List next page? {CONFIRM_CHOICE_STRING}")
                if current_page_number != len(pages):
                    if pages.index(page) + 1 != len(pages):
                        if user_confirm in {"y", "yes", ""}:
                            continue
                        else:
                            break
    if args.download:
        yadisk.download(args.id)
    if args.upload:
        yadisk.upload(args.directory, f"/{os.path.split(args.directory)[1]}")


def print_gdrive_file(file):
    default_view = file.name + " " + f"({file.id})"
    if file.mime_type == "application/vnd.google-apps.folder":
        print("".join(Fore.CYAN + default_view + Style.RESET_ALL))
    else:
        print(default_view)


def print_yadisk_file(file):
    default_view = file.name + " " + f"({file.path})"
    if file.mime_type == file.type == "dir":
        print("".join(Fore.CYAN + default_view + Style.RESET_ALL))
    else:
        print(default_view)


def main():
    init()
    args = parse_args()
    if args.storage == "gdrive":
        handle_gdrive(args)
    elif args.storage == "yadisk":
        handle_yadisk(args)
    else:
        print(f"Unrecognized storage name: {args.storage}")


if __name__ == "__main__":
    main()
