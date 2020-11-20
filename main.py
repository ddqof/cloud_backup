#!/usr/bin/env python3

import os
from colorama import init, Fore, Style
from cloudbackup.gdrive import GDrive
from cloudbackup.yadisk import YaDisk
from cloudbackup._parser import parse_args
from cloudbackup._defaults import YADISK_SORT_KEYS, GDRIVE_SORT_KEYS
from cloudbackup._exceptions import RemoteFileNotFoundException


def handle_gdrive(args):
    gdrive = GDrive()
    try:
        file = gdrive.get_file_object_by_id(args.id)
        file_id = file.id
    except RemoteFileNotFoundException:
        file_id = None
    if args.list:
        pages = gdrive.lsdir(dir_id=file_id, page_size=20, order_by=GDRIVE_SORT_KEYS[args.order_by])
        for page in pages:
            for file in page:
                default_view = file.name + " " + f"({file.id})"
                if file.mime_type == "application/vnd.google-apps.folder":
                    print("".join(Fore.CYAN + default_view + Style.RESET_ALL))
                else:
                    print(default_view)
            user_confirm = input("List next page? [y/n] ")
            if user_confirm in {"y", "yes"}:
                continue
            else:
                break
    if args.download:
        print(gdrive.download(file, path=args.directory))
    if args.upload:
        print(gdrive.upload(args.directory))
    if args.remove:
        if args.permanently:
            user_confirm = input(f"Are you sure you want to delete {file.name} file? [y/n] ")
            if user_confirm in {"y", "yes"}:
                print(gdrive.remove(file_id=file.id))
            else:
                print("Aborted")
        else:
            user_confirm = input(f"Are you sure you want to move {file.name} to trash? [y/n] ")
            if user_confirm in {"y", "yes"}:
                print(gdrive.remove(file_id=file.id))
            else:
                print("Aborted")


def handle_yadisk(args):
    yadisk = YaDisk()
    if args.list:
        path = args.id
        if args.id == "root":
            path = "/"
        if path is None:
            pages = yadisk.list_files(sort=YADISK_SORT_KEYS[args.order_by])
        else:
            pages = yadisk.lsdir(path, sort=YADISK_SORT_KEYS[args.order_by])
        for page in pages:
            for file in page:
                default_view = file.name + " " + f"({file.path})"
                if file.type == "dir":
                    print("".join(Fore.CYAN + default_view + Style.RESET_ALL))
                else:
                    print(default_view)
            user_confirm = input("List next page? [y/n] ")
            if user_confirm in {"y", "yes"}:
                continue
            else:
                break
    if args.download:
        yadisk.download(args.id)
    if args.upload:
        yadisk.upload(args.directory, f"/{os.path.split(args.directory)[1]}")


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
