#!/usr/bin/env python3

import argparse


def parse_args():
    parser = argparse.ArgumentParser(
        usage=" ./main.py [-s storage_name] STORAGE_NAME [-ls list_files]  [-o order_by]\n\t"
              " [-dl download_file] [-rm remove_file] [-p remove_permanently_flag]\n\t"
              " [-ul upload_file] [-id file_id] ID [-d directory] PATH",
        prog="main.py",
        description="""Tool for operate with your files on Google Drive or YandexDisk storage""",
        epilog="""Author: Dmitry Podaruev <ddqof.vvv@gmail.com>"""
    )
    parser.add_argument("-s", "--storage",
                        metavar="",
                        help="specify remote storage name"
                             " (gdrive, yadisk)",
                        required=True,
                        type=str)
    parser.add_argument("-ls", "--list",
                        action="store_true",
                        help="List files"
                             " (if path not specified list all files)")
    parser.add_argument("-dl", "--download",
                        action="store_true",
                        help="download file")
    parser.add_argument("-d", "--directory",
                        metavar="",
                        help="Specify directory and pass it with -dl argument "
                             "to download file to specific directory")
    parser.add_argument("-rm", "--remove",
                        action="store_true",
                        help="Remove file")
    parser.add_argument("-p", "--permanently",
                        action="store_true",
                        help="Delete file permanently")
    parser.add_argument("-ul", "--upload",
                        action="store_true",
                        help="Upload file")
    parser.add_argument("-id",
                        metavar="",
                        help="Id of file in Google Drive storage or file path in YandexDisk")
    parser.add_argument("-o", "--order_by",
                        metavar="",
                        default="modified",
                        help="Sort key for file listing. Available keys are: "
                             "'name', 'created', 'modified', 'size'."
                             " Also 'folder' (will show folders first) for GDrive only and 'path'"
                             " (will sort by path) for YaDisk only. To sort in "
                             "reversed order add prefix 'rev'. For example: 'rev_name'.")

    return parser.parse_args()
