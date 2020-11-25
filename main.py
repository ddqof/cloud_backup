#!/usr/bin/env python3

import sys
from colorama import init, Fore, Style
from cloudbackup.gdrive import GDrive
from cloudbackup.yadisk import YaDisk
from cloudbackup.exceptions import RemoteFileNotFoundException, ApiResponseException
from defaults import (GDRIVE_SORT_KEYS,
                      YADISK_SORT_KEYS,
                      ABORTED_MSG,
                      SUCCESSFUL_DOWNLOAD_MSG,
                      SUCCESSFUL_UPLOAD_MSG,
                      SUCCESSFUL_DELETE_MSG,
                      SUCCESSFUL_TRASH_MSG,
                      MOVE_TO_TRASH_CONFIRMATION_MSG,
                      DELETE_CONFIRMATION_MSG,
                      LIST_NEXT_PAGE_MSG)
from parser import parse_args


def handle_gdrive(args):
    gdrive = GDrive()
    if args.remote_file:
        try:
            file = gdrive.get_file_object_by_id(args.remote_file)
        except RemoteFileNotFoundException as e:
            print(e)
            sys.exit(1)
    if args.operation == "ls":
        if args.remote_file is None:
            try:
                files = gdrive.get_all_files(owners=['me'])
            except ApiResponseException as e:
                print(e)
                sys.exit(1)
            for file in files:
                print_gdrive_file(file)
        else:
            if file.mime_type != "application/vnd.google-apps.folder":
                print_gdrive_file(file)
            else:
                while True:
                    try:
                        page = gdrive.lsdir(dir_id=file.id, owners=['me'], page_size=20,
                                            order_by=GDRIVE_SORT_KEYS[args.order_by])
                    except ApiResponseException as e:
                        print(e)
                        sys.exit(1)
                    for file in page.files:
                        print_gdrive_file(file)
                    if page.next_page_token is not None:
                        user_confirm = input(LIST_NEXT_PAGE_MSG)
                        if user_confirm in {"y", "yes", ""}:
                            continue
                        else:
                            print(ABORTED_MSG)
                            break
                    else:
                        break
    elif args.operation == "dl":
        gdrive.download(file, destination=args.destination, overwrite=args.overwrite)
        print(SUCCESSFUL_DOWNLOAD_MSG.format(file_name=file.name))
    elif args.operation == "ul":
        gdrive.upload(args.file_name)
        print(SUCCESSFUL_UPLOAD_MSG.format(file_name=args.local_file))
    elif args.operation == "rm":
        if args.permanently:
            user_confirm = input(DELETE_CONFIRMATION_MSG.format(file_name=file.name))
            if user_confirm in {"y", "yes", ""}:
                try:
                    gdrive.remove(file_id=file.id, permanently=True)
                except ApiResponseException as e:
                    print(e)
                    sys.exit(1)
                print(SUCCESSFUL_DELETE_MSG.format(file_name=file.name))

            else:
                print(ABORTED_MSG)
        else:
            user_confirm = input(MOVE_TO_TRASH_CONFIRMATION_MSG.format(file_name=file.name))
            if user_confirm in {"y", "yes", ""}:
                try:
                    gdrive.remove(file_id=file.id)
                except ApiResponseException as e:
                    print(e)
                    sys.exit(1)
                print(SUCCESSFUL_TRASH_MSG.format(file_name=file.name))
            else:
                print(ABORTED_MSG)


def handle_yadisk(args):
    yadisk = YaDisk()
    if args.operation == "ls":
        path = args.remote_file
        if path == "root":
            path = "/"
        offset = 0
        if path is None:
            limit, all_files = 1000, []
            while True:
                try:
                    page_files = yadisk.list_files(limit=limit, sort=YADISK_SORT_KEYS[args.order_by], offset=offset)
                except ApiResponseException as e:
                    print(e)
                    sys.exit(1)
                if page_files:
                    all_files.extend(page_files)
                    offset += limit
                else:
                    break
            for file in all_files:
                print_yadisk_file(file)
        else:
            try:
                page_files = yadisk.lsdir(path, offset=offset, sort=YADISK_SORT_KEYS[args.order_by])
            except ApiResponseException as e:
                print(e)
                sys.exit(1)
            while True:
                for file in page_files:
                    print_yadisk_file(file)
                offset += 20
                try:
                    page_files = yadisk.lsdir(path, offset=offset, sort=YADISK_SORT_KEYS[args.order_by])
                except ApiResponseException as e:
                    print(e)
                    sys.exit(1)
                if not page_files:
                    break
                user_confirm = input(LIST_NEXT_PAGE_MSG)
                if user_confirm in {"y", "yes", ""}:
                    continue
                else:
                    break
    elif args.operation == "dl":
        try:
            yadisk.download(args.remote_file)
        except ApiResponseException as e:
            print(e)
            sys.exit(1)
    elif args.operation == "ul":
        try:
            yadisk.upload(args.local_file)
        except ApiResponseException as e:
            print(sys.exit(1))
    elif args.operation == "rm":
        if args.permanently:
            user_confirm = input(DELETE_CONFIRMATION_MSG.format(file_name=args.remote_file))
            if user_confirm in {"y", "yes", ""}:
                try:
                    yadisk.remove(args.remote_file, permanently=False)
                except ApiResponseException as e:
                    print(e)
                    sys.exit(1)
                print(SUCCESSFUL_DELETE_MSG.format(file_name=args.remote_file))
            else:
                print(ABORTED_MSG)
        else:
            user_confirm = input(MOVE_TO_TRASH_CONFIRMATION_MSG.format(file_name=args.remote_file))
            if user_confirm in {"y", "yes", ""}:
                try:
                    yadisk.remove(args.remote_file, permanently=True)
                except ApiResponseException as e:
                    print(e)
                    sys.exit(1)
                print(SUCCESSFUL_TRASH_MSG.format(file_name=args.remote_file))
            else:
                print(ABORTED_MSG)


def print_gdrive_file(file):
    default_view = file.name + " " + f"({file.id})"
    if file.mime_type == "application/vnd.google-apps.folder":
        print("".join(Fore.CYAN + default_view + Style.RESET_ALL))
    else:
        print(default_view)


def print_yadisk_file(file):
    default_view = file.name + " " + f"({file.path})"
    if file.type == "dir":
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


if __name__ == "__main__":
    main()
