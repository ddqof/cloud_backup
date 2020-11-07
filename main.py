#!/usr/bin/env python3

import argparse
from colorama import init, Fore, Style
from cloudbackup.gdrive import GDrive


def parse_args():
    parser = argparse.ArgumentParser(
        usage="[-s] STORAGE_NAME [-dl] [-ls] [-rm] [-ul] [-id] ID [-p] PATH",
        prog="main.py",
        description="""Tool for operate with your files on Google Drive storage""",
        epilog="""Author: Dmitry Podaruev <ddqof.vvv@gmail.com>"""
    )
    parser.add_argument("-s", "--storage",
                        metavar="",
                        help="specify remote storage name"
                             "(examples: gdrive, yadisk)",
                        type=str)
    parser.add_argument("-ls", "--list",
                        action="store_true",
                        help="list files"
                             "(if path not specified list all files)")
    parser.add_argument("-dl", "--download",
                        action="store_true",
                        help="download file")
    parser.add_argument("-p", "--path",
                        metavar="",
                        help="specify path and pass it with -dl argument "
                             "to download file to specific directory")
    parser.add_argument("-rm", '--remove',
                        action="store_true",
                        help="remove file "
                             "(be careful! it deletes without ability to restore)")
    parser.add_argument("-ul", "--upload",
                        action="store_true",
                        help="upload file")
    parser.add_argument("-id",
                        metavar="",
                        help="id of file in Google Drive storage")

    return parser.parse_args()


def cli_handler(args):
    gdrive = GDrive()
    if args.list:
        files = gdrive.list_files(gdrive.autocomplete_id(args.id))
        for filename in files:
            default_view = filename["name"] + " " + f"({filename['id']})"
            if filename["mimeType"] == "application/vnd.google-apps.folder":
                print("".join(Fore.CYAN + default_view + Style.RESET_ALL))
            else:
                print(default_view)
    if args.download:
        print(gdrive.download(gdrive.autocomplete_id(args.id), path=args.path))
    if args.upload:
        print(gdrive.upload(file_abs_path=args.path))
    if args.remove:
        print(gdrive.delete(file_id=gdrive.autocomplete_id(args.id)))


def main():
    init()
    cli_handler(parse_args())


if __name__ == "__main__":
    main()
