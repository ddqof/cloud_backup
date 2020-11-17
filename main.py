#!/usr/bin/env python3

import os
from colorama import init, Fore, Style
from cloudbackup.gdrive import GDrive
from cloudbackup.yadisk import YaDisk
from cloudbackup._parser import parse_args


def cli_handler(args):
    if args.storage == "gdrive":
        gdrive = GDrive()
        if args.list:
            files = []
            if args.id is None:
                files = gdrive.files
            else:
                for page in gdrive.lsdir(dir_id=gdrive.autocomplete_id(args.id), page_size=1000,
                                         order_by='createdTime'):
                    files.extend(page)
            for file in files:
                default_view = file.name + " " + f"({file.id})"
                if file.mime_type == "application/vnd.google-apps.folder":
                    print("".join(Fore.CYAN + default_view + Style.RESET_ALL))
                else:
                    print(default_view)
        if args.download:
            print(gdrive.download(gdrive.autocomplete_id(args.id), path=args.directory))
        if args.upload:
            print(gdrive.upload(file_abs_path=args.directory))
        if args.remove:
            request_file_id = gdrive.autocomplete_id(args.id)
            for file in gdrive.files:
                if file.id == request_file_id:
                    user_confirm = input(f"Are you sure you want to delete {file.name} file? [y/n] ")
                    if user_confirm in {"y", "yes"}:
                        print(gdrive.remove(file_id=request_file_id))
                    else:
                        print("Aborted")

    if args.storage == "yadisk":
        yadisk = YaDisk()
        if args.list:
            path = args.id
            if args.id == "root":
                path = "/"
            files = yadisk.lsdir(path)
            for file in files:
                default_view = file.name + " " + f"({file.path})"
                if file.type == "dir":
                    print("".join(Fore.CYAN + default_view + Style.RESET_ALL))
                else:
                    print(default_view)
        if args.download:
            yadisk.download(args.id)
        if args.upload:
            yadisk.upload(args.path, f"/{os.path.split(args.path)[1]}")


def main():
    init()
    cli_handler(parse_args())


if __name__ == "__main__":
    main()
