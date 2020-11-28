#!/usr/bin/env python3

import sys
import os
from colorama import init
from cloudbackup.gdrive import GDrive
from cloudbackup.yadisk import YaDisk
from cloudbackup.exceptions import (IncorrectPathException,
                                    ApiResponseException,
                                    FileIsNotDownloadableException)
from defaults import (SUCCESSFUL_DOWNLOAD_MSG,
                      SUCCESSFUL_UPLOAD_FILE_MSG,
                      SUCCESSFUL_UPLOAD_DIR_MSG)
from parser import parse_args
from gdrive_wrapper import GDriveWrapper
from yadisk_wrapper import YaDiskWrapper


def handle_gdrive(args):
    gdrive = GDrive()
    wrapper = GDriveWrapper(gdrive)
    try:
        if hasattr(args, "remote_file") and args.remote_file is not None:
            file = wrapper.get_file_object_by_id(args.remote_file)
        else:
            file = None
        if args.operation == "ls":
            wrapper.lsdir(file, args.order_by)
        elif args.operation == "dl":
            wrapper.download(file, destination=args.destination, overwrite=args.overwrite)
            print(SUCCESSFUL_DOWNLOAD_MSG.format(file_name=file.name))
        elif args.operation == "ul":
            wrapper.upload(args.local_file)
            print_successful_upload_msg(args.local_file)
        elif args.operation == "rm":
            wrapper.remove(file, permanently=args.permanently)
    except (ApiResponseException,
            FileExistsError,
            FileNotFoundError,
            ValueError) as e:
        print(e)
        sys.exit(1)
    except KeyboardInterrupt:
        print("Interrupted by user.")
        sys.exit(1)


def handle_yadisk(args):
    yadisk = YaDisk()
    wrapper = YaDiskWrapper(yadisk)
    try:
        if args.operation == "ls":
            wrapper.lsdir(args.remote_file, order_key=args.order_by)
        elif args.operation == "dl":
            wrapper.download(args.remote_file, destination=args.destination, overwrite=args.overwrite)
        elif args.operation == "ul":
            wrapper.upload(args.local_file)
            print_successful_upload_msg(args.local_file)
        elif args.operation == "rm":
            wrapper.remove(args.remote_file, permanently=args.permanently)
    except (ApiResponseException,
            FileNotFoundError,
            FileExistsError,
            IncorrectPathException,
            FileIsNotDownloadableException,
            PermissionError) as e:
        print(e)
        sys.exit(1)
    except KeyboardInterrupt:
        print("Interrupted by user.")
        sys.exit(1)


def print_successful_upload_msg(file_path):
    if os.path.isfile(file_path):
        print(SUCCESSFUL_UPLOAD_FILE_MSG.format(file_name=file_path ))
    elif os.path.isdir(file_path):
        print(SUCCESSFUL_UPLOAD_DIR_MSG.format(dir_name=file_path))


def main():
    init()
    args = parse_args()
    if args.storage == "gdrive":
        handle_gdrive(args)
    elif args.storage == "yadisk":
        handle_yadisk(args)


if __name__ == "__main__":
    main()
