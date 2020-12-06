#!/usr/bin/env python3

import sys
from colorama import init
from cloudbackup.gdrive import GDrive
from cloudbackup.yadisk import YaDisk
from cloudbackup.exceptions import ApiResponseException
from defaults import (DOWNLOAD_COMPLETED_MSG,
                      UPLOAD_COMPLETED_MSG, UNEXPECTED_VALUE_MSG)
from parser import parse_args
from gdrive_wrapper import GDriveWrapper
from yadisk_wrapper import YaDiskWrapper


def main():
    exit_msg = None
    init()
    args = parse_args()
    if args.storage == "gdrive":
        storage = GDrive()
        wrapper = GDriveWrapper(storage)
    elif args.storage == "yadisk":
        storage = YaDisk()
        wrapper = YaDiskWrapper(storage)
    else:
        error_msg = UNEXPECTED_VALUE_MSG.format(
            var_name=f"{args.storage=}".split("=")[0],
            value=args.storage,
        )
        raise ValueError(error_msg)
    try:
        if args.operation == "ls":
            wrapper.lsdir(args.remote_file, order_key=args.order_by)
        elif args.operation == "dl":
            if isinstance(storage, GDrive):
                remote_file = wrapper.get_file_object_by_id(args.remote_file)
            elif isinstance(storage, YaDisk):
                remote_file = args.remote_file
            wrapper.download(
                file=remote_file,
                local_destination=args.destination,
                overwrite=args.overwrite
            )
            exit_msg = DOWNLOAD_COMPLETED_MSG
        elif args.operation == "ul":
            wrapper.upload(args.local_file)
            exit_msg = UPLOAD_COMPLETED_MSG
        elif args.operation == "rm":
            wrapper.remove(args.remote_file, permanently=args.permanently)
        if exit_msg:
            print(exit_msg)
    except (ApiResponseException,
            FileExistsError,
            FileNotFoundError,
            PermissionError) as e:
        print(e)
        sys.exit(1)
    except KeyboardInterrupt:
        print("Interrupted by user.")
        sys.exit(1)


if __name__ == "__main__":
    main()
