#!/usr/bin/env python3

import common_operations
import sys
import os
from colorama import init
from cloudbackup.gdrive import GDrive
from cloudbackup.yadisk import YaDisk
from cloudbackup.exceptions import ApiResponseException
from defaults import (SUCCESSFUL_DOWNLOAD_FILE_MSG,
                      SUCCESSFUL_UPLOAD_FILE_MSG,
                      SUCCESSFUL_UPLOAD_DIR_MSG,
                      GDRIVE_DIRECTORY_TYPE,
                      SUCCESSFUL_DOWNLOAD_DIR_MSG,
                      UNEXPECTED_VALUE_MSG)
from parser import parse_args
from gdrive_wrapper import GDriveWrapper
from yadisk_wrapper import YaDiskWrapper


def print_successful_upload_msg(file_path):
    if os.path.isfile(file_path):
        print(SUCCESSFUL_UPLOAD_FILE_MSG.format(file_name=file_path))
    elif os.path.isdir(file_path):
        print(SUCCESSFUL_UPLOAD_DIR_MSG.format(dir_name=file_path))


def main():
    init()
    args = parse_args()
    if args.storage == "gdrive":
        storage = GDrive()
        wrapper = GDriveWrapper(storage)
        if args.operation in {"ls", "dl", "rm"} and args.remote_file:
            remote_file = common_operations.get_file_object_by_id(storage, args.remote_file)
    elif args.storage == "yadisk":
        storage = YaDisk()
        wrapper = YaDiskWrapper(storage)
        remote_file = storage.lsdir(args.remote_file).file_info
    else:
        error_msg = common_operations.get_unexpected_value_msg(args.storage)
        raise ValueError(error_msg)

    try:
        if args.operation == "ls":
            wrapper.lsdir(args.remote_file, order_key=args.order_by)
        elif args.operation == "dl":
            common_operations.download(storage,
                                       remote_destination=remote_file.path,
                                       file_name=remote_file.name,
                                       file_type=remote_file.type,
                                       local_destination=args.destination,
                                       overwrite=args.overwrite)
            if remote_file.type == "dir":
                exit_msg = SUCCESSFUL_DOWNLOAD_DIR_MSG.format(dir_name=remote_file.name)
            elif remote_file == "file":
                exit_msg = SUCCESSFUL_DOWNLOAD_FILE_MSG.format(file_name=remote_file.name)
            print(exit_msg)
        elif args.operation == "ul":
            wrapper.upload(args.local_file)
        elif args.operation == "rm":
            wrapper.remove(args.remote_file, permanently=args.permanently)
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
