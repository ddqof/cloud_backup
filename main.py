#!/usr/bin/env python3

import sys

from cloudbackup.exceptions import ApiResponseException
from defaults import (DOWNLOAD_COMPLETED_MSG,
                      UPLOAD_COMPLETED_MSG)
from parser import parse_args
from gdrive_wrapper import GDriveWrapper
from yadisk_wrapper import YaDiskWrapper


def main():
    exit_msg = None
    args = parse_args()
    if args.storage == "gdrive":
        wrapper = GDriveWrapper()
    else:
        wrapper = YaDiskWrapper()
    try:
        if args.operation == "ls":
            wrapper.lsdir(args.remote_file, order_key=args.order_by)
        elif args.operation == "dl":
            wrapper.download(
                args.remote_file,
                local_destination=args.destination,
                overwrite=args.overwrite
            )
            exit_msg = DOWNLOAD_COMPLETED_MSG
        elif args.operation == "ul":
            wrapper.upload(args.local_file, args.destination)
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
