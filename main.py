#!/usr/bin/env python3

import sys
from colorama import init
from cloudbackup.gdrive import GDrive
from cloudbackup.yadisk import YaDisk
from cloudbackup.exceptions import IncorrectPathException, ApiResponseException
from defaults import (SUCCESSFUL_DOWNLOAD_MSG,
                      SUCCESSFUL_UPLOAD_MSG)
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
            print(SUCCESSFUL_UPLOAD_MSG.format(file_name=args.local_file))
        elif args.operation == "rm":
            wrapper.remove(file, permanently=args.permanently)
    except (ApiResponseException,
            ValueError,
            FileExistsError,
            FileNotFoundError) as e:
        print(e)
        sys.exit(1)


def handle_yadisk(args):
    yadisk = YaDisk()
    wrapper = YaDiskWrapper(yadisk)
    try:
        if args.operation == "ls":
            wrapper.lsdir(args.remote_file, order_key=args.order_by)
        elif args.operation == "dl":
            wrapper.download(args.remote_file, args.destination)
        elif args.operation == "ul":
            wrapper.upload(args.local_file)
        elif args.operation == "rm":
            wrapper.remove(args.remote_file, permanently=args.permanently)
    except (ApiResponseException,
            FileNotFoundError,
            IncorrectPathException) as e:
        print(e)
        sys.exit(1)


def main():
    init()
    args = parse_args()
    if args.storage == "gdrive":
        handle_gdrive(args)
    elif args.storage == "yadisk":
        handle_yadisk(args)


if __name__ == "__main__":
    main()
