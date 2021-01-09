import argparse


def parse_args():
    parser = argparse.ArgumentParser(
        description=("""Tool for operate with your files on
         Google Drive or YandexDisk storage."""),
        epilog="""Author: Dmitry Podaruev <ddqof.vvv@gmail.com>""")
    parser.add_argument(
        "storage",
        help="remote storage name",
        choices=["gdrive", "yadisk"])

    subparsers = parser.add_subparsers(
        title="available operations",
        help="operation",
        dest="operation",
        required=True)
    # for preventing repeat of file arg
    remote_file_parser = argparse.ArgumentParser(add_help=False)
    remote_file_parser.add_argument(
        "remote_file",
        help="If work with GDrive pass file (directory) id."
             " If work with YaDisk pass file (directory) path.")

    ls_parser = subparsers.add_parser("ls",
                                      help="list a directory")
    ls_parser.add_argument(
        "remote_file",
        nargs="?",
        help="If work with GDrive pass directory id. If work with YaDisk"
             " pass directory path. If not specified listing all files.")
    ls_parser.add_argument(
        '-o', "--order_by",
        default="modified",
        choices=[
            "name", "created", "modified", "size", "folder", "path",
            "rev_name", "rev_created", "rev_modified", "rev_size",
            "rev_folder", "rev_path",
        ],
        metavar="",
        help="Sort key for file listing. Available keys are: "
             "'name', 'created', 'modified', 'size'."
             " Also 'folder' (will show folders first) for GDrive only and"
             " 'path' (will sort by path) for YaDisk only. To sort in"
             " reversed order add previx 'rev'. For example: 'rev_name'.")

    dl_parser = subparsers.add_parser(
        "dl",
        help="download a file or directory",
        parents=[remote_file_parser])
    dl_parser.add_argument(
        "destination",
        nargs="?",
        help="Pass directory where you want to save downloaded file."
             " If not specified download to present working directory.")
    dl_parser.add_argument(
        "-ov", "--overwrite",
        action="store_true",
        help="overwrite if file already exists")
    dl_parser.add_argument(
        "-f", "--force",
        action="store_true",
        help="skip G.Suite files when downloading a directory")

    ul_parser = subparsers.add_parser(
        "ul",
        help="upload a file or directory")
    ul_parser.add_argument(
        "local_file",
        help="pass local filename")
    ul_parser.add_argument(
        "destination",
        nargs="?",
        help="pass destination at remote storage")

    rm_parser = subparsers.add_parser(
        "rm",
        help="remove a file",
        parents=[remote_file_parser])
    rm_parser.add_argument(
        "-p", "--permanently",
        action="store_true",
        help="permanently delete file skipping the trash")

    return parser.parse_args()
