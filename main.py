#!/usr/bin/env python3

import common_operations
import sys
import os
from colorama import init
from cloudbackup.gdrive import GDrive
from cloudbackup.yadisk import YaDisk
from cloudbackup.exceptions import ApiResponseException
from defaults import (SUCCESSFUL_DOWNLOAD_FILE_MSG,
                      GDRIVE_DIRECTORY_TYPE,
                      SUCCESSFUL_DOWNLOAD_DIR_MSG,
                      UNEXPECTED_VALUE_MSG, DOWNLOAD_COMPLETED_MSG, UPLOAD_COMPLETED_MSG, SUCCESSFUL_UPLOAD_FILE_MSG,
                      SUCCESSFUL_UPLOAD_DIR_MSG)
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
        error_msg = common_operations.get_unexpected_value_msg(args.storage)
        raise ValueError(error_msg)

    try:
        if args.operation == "ls":
            wrapper.lsdir(args.remote_file, order_key=args.order_by)
        # elif args.operation == "dl":
        #     common_operations.download(storage,
        #                                remote_target=args.remote_file,
        #                                local_destination=args.destination,
        #                                overwrite=args.overwrite)
        #     exit_msg = DOWNLOAD_COMPLETED_MSG
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
