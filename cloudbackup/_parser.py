#!/usr/bin/env python3

import argparse


def parse_args():
    parser = argparse.ArgumentParser(
        usage=" ./main.py [-s storage_name] STORAGE_NAME [-dl download_file] [-ls list_files]\n\t"
              " [-o order_by] [-rm remove_file] [-p remove_permanently_flag]\n\t"
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
                        help="list files"
                             " (if path not specified list all files)")
    parser.add_argument("-dl", "--download",
                        action="store_true",
                        help="download file")
    parser.add_argument("-d", "--directory",
                        metavar="",
                        help="specify directory and pass it with -dl argument "
                             "to download file to specific directory")
    parser.add_argument("-rm", '--remove',
                        action="store_true",
                        help="remove file")
    parser.add_argument("-p", "--permanently",
                        action="store_true",
                        help="delete file permanently")
    parser.add_argument("-ul", "--upload",
                        action="store_true",
                        help="upload file")
    parser.add_argument("-id",
                        metavar="",
                        help="id of file in Google Drive storage")
    # TODO: add list orderBy argument

    return parser.parse_args()
