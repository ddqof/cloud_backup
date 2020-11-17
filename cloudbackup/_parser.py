#!/usr/bin/env python3

import argparse


def parse_args():
    parser = argparse.ArgumentParser(
        usage="[-s] STORAGE_NAME [-dl] [-ls] [-rm] [-ul] [-id] ID [-d] PATH",
        prog="main.py",
        description="""Tool for operate with your files on Google Drive storage""",
        epilog="""Author: Dmitry Podaruev <ddqof.vvv@gmail.com>"""
    )
    parser.add_argument("-s", "--storage",
                        metavar="",
                        help="specify remote storage name"
                             "(examples: gdrive, yadisk)",
                        required=True,
                        type=str)
    parser.add_argument("-ls", "--list",
                        action="store_true",
                        help="list files"
                             "(if path not specified list all files)")
    parser.add_argument("-dl", "--download",
                        action="store_true",
                        help="download file")
    parser.add_argument("-d", "--directory",
                        metavar="",
                        help="specify directory and pass it with -dl argument "
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
    parser.add_argument()

    return parser.parse_args()
