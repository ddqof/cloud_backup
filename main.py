#!/usr/bin/env python3

import os
from colorama import init, Fore, Style
from cloudbackup.gdrive import GDrive
from cloudbackup.yadisk import YaDisk
from cloudbackup.exceptions import RemoteFileNotFoundException, FileIsNotDownloadableException
from defaults import (GDRIVE_SORT_KEYS, YADISK_SORT_KEYS, CONFIRM_CHOICE_STRING,
                      ABORTED_MSG, SUCCESSFUL_DOWNLOAD_MSG, SUCCESSFUL_UPLOAD_MSG,
                      SUCCESSFUL_DELETE_MSG, SUCCESSFUL_TRASH_MSG, G_SUITE_DIRECTORY,
                      G_SUITE_FILE)
from parser import parse_args


def handle_gdrive(args):
    gdrive = GDrive()
    if args.list:
        if args.id is None:
            files = gdrive.get_all_files(owners=['me'])
            for file in files:
                print_gdrive_file(file)
        else:
            while True:
                file = gdrive.get_file_object_by_id(args.id)
                page = gdrive.lsdir(dir_id=file.id, owners=['me'], page_size=20,
                                    order_by=GDRIVE_SORT_KEYS[args.order_by])
                for file in page.files:
                    print_gdrive_file(file)
                if page.next_page_token is not None:
                    user_confirm = input(f"List next page? {CONFIRM_CHOICE_STRING}")
                    if user_confirm in {"y", "yes", ""}:
                        continue
                    else:
                        print(ABORTED_MSG)
                        break
                else:
                    break
    if args.download:
        file = gdrive.get_file_object_by_id(args.id)
        try:
            gdrive.download(file, path=args.directory, )
        except FileIsNotDownloadableException:
            if file.mime_type == "application/vnd.google-apps.folder":
                print(G_SUITE_DIRECTORY.format(file_name=file.name))
            else:
                print(G_SUITE_FILE.format(file_name=file.name))
        print(SUCCESSFUL_DOWNLOAD_MSG.format(file_name=file.name))
    if args.upload:
        gdrive.upload(args.directory)
        print(SUCCESSFUL_UPLOAD_MSG.format(file_name=args.directory))
    if args.remove:
        file = gdrive.get_file_object_by_id(args.id)
        if args.permanently:
            user_confirm = input(f"Are you sure you want to delete {file.name} file? {CONFIRM_CHOICE_STRING}")
            if user_confirm in {"y", "yes", ""}:
                gdrive.remove(file_id=file.id, permanently=True)
                print(SUCCESSFUL_DELETE_MSG.format(file_name=file.name))

            else:
                print(ABORTED_MSG)
        else:
            user_confirm = input(f"Are you sure you want to move {file.name} to trash? {CONFIRM_CHOICE_STRING}")
            if user_confirm in {"y", "yes", ""}:
                gdrive.remove(file_id=file.id)
                print(SUCCESSFUL_TRASH_MSG.format(file_name=file.name))
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
