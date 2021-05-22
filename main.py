#!/usr/bin/env python3

import sys
from pathlib import Path

from arg_parser import parse_args
from cloudbackup.exceptions import ApiResponseException, CredentialsNotFoundException
from wrappers.defaults import (DOWNLOAD_COMPLETED_MSG,
                               UPLOAD_COMPLETED_MSG)
from wrappers.gdrive_wrapper import GDriveWrapper
from wrappers.yadisk_wrapper import YaDiskWrapper


def main():
    exit_msg = None
    args = parse_args()
    try:
        if args.storage == "gdrive":
            wrapper = GDriveWrapper()
        else:
            wrapper = YaDiskWrapper()
        if args.operation == "ls":
            wrapper.lsdir(args.remote_file, order_key=args.order_by)
        elif args.operation == "dl":
            wrapper.download(
                wrapper.get_file(args.remote_file),
                local_destination=Path(args.destination),
                ov=args.overwrite
            )
            exit_msg = DOWNLOAD_COMPLETED_MSG
        elif args.operation == "ul":
            wrapper.upload(Path(args.local_file), args.destination)
            exit_msg = UPLOAD_COMPLETED_MSG
        elif args.operation == "rm":
            wrapper.remove(args.remote_file, permanently=args.permanently)
        if exit_msg:
            print(exit_msg)
    except (ApiResponseException,
            FileExistsError,
            FileNotFoundError,
            PermissionError,
            CredentialsNotFoundException
            ) as e:
        print(e)
        sys.exit(1)
    except KeyboardInterrupt:
        print("Interrupted by user.")
        sys.exit(1)


if __name__ == "__main__":
    main()
