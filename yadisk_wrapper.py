import errno
import os
import shutil
from colorama import Fore, Style
from defaults import (YADISK_SORT_KEYS,
                      ABORTED_MSG,
                      SUCCESSFUL_DELETE_MSG,
                      SUCCESSFUL_TRASH_MSG,
                      MOVE_TO_TRASH_CONFIRMATION_MSG,
                      DELETE_CONFIRMATION_MSG,
                      LIST_NEXT_PAGE_MSG,
                      OVERWRITING_DIRECTORY_MSG,
                      OVERWRITE_REQUEST_MSG,
                      MAKING_DIRECTORY_MSG,
                      DOWNLOADING_FILE_MSG,
                      UPLOADING_FILE_MSG,
                      UPLOADING_DIRECTORY_MSG, SUCCESSFUL_DOWNLOAD_MSG, DOWNLOADING_DIR_AS_ZIP_MSG)
from cloudbackup.yadisk import YaDisk


class YaDiskWrapper:

    def __init__(self, yadisk: YaDisk):
        self._yadisk = yadisk

    def lsdir(self, path, order_key=None):
        if path == "root":
            path = "/"
        offset = 0
        if path is None:
            limit, all_files = 1000, []
            while True:
                page_files = self._yadisk.list_files(limit=limit, sort=YADISK_SORT_KEYS[order_key], offset=offset)
                if page_files:
                    all_files.extend(page_files)
                    offset += limit
                else:
                    break
            for file in all_files:
                YaDiskWrapper.print(file)
        else:
            page_files = self._yadisk.lsdir(path, offset=offset, sort=YADISK_SORT_KEYS[order_key])
            while True:
                for file in page_files:
                    YaDiskWrapper.print(file)
                offset += 20
                page_files = self._yadisk.lsdir(path, offset=offset, sort=YADISK_SORT_KEYS[order_key])
                if not page_files:
                    break
                user_confirm = input(LIST_NEXT_PAGE_MSG)
                if user_confirm in {"y", "yes", ""}:
                    continue
                else:
                    break

    def upload(self, file_abs_path, destination="/") -> None:
        """
        Upload file to YandexDisk storage

        Args:
            file_abs_path: absolute path of file.
            destination: where to store uploaded file on YandexDisk.

        Raises:
            ApiResponseException: an error occurred accessing API.
        """
        if os.path.isfile(file_abs_path):
            self._yadisk.single_upload(file_abs_path, destination)
        elif os.path.isdir(file_abs_path):
            if file_abs_path.endswith(os.path.sep):
                file_abs_path = file_abs_path[:-1]
            tree = os.walk(file_abs_path)
            head = os.path.split(file_abs_path)[0]
            for root, dirs, filenames in tree:
                destination = root.split(head)[1]
                print(UPLOADING_DIRECTORY_MSG.format(file_name=destination))
                self._yadisk.mkdir(destination)
                if not filenames:
                    continue
                for file in filenames:
                    ul_path = os.path.join(root, file)
                    print(UPLOADING_FILE_MSG.format(file_name=ul_path))
                    self._yadisk.single_upload(ul_path, f"{destination}/{file}")
        else:
            raise FileNotFoundError(errno.ENOENT, os.strerror(errno.ENOENT), file_abs_path)

    def remove(self, path, permanently=False):
        if permanently:
            user_confirm = input(DELETE_CONFIRMATION_MSG.format(file_name=path.name))
            if user_confirm in {"y", "yes", ""}:
                self._yadisk.remove(path, permanently=True)
                print(SUCCESSFUL_DELETE_MSG.format(file_name=path))

            else:
                print(ABORTED_MSG)
        else:
            user_confirm = input(MOVE_TO_TRASH_CONFIRMATION_MSG.format(file_name=path))
            if user_confirm in {"y", "yes", ""}:
                self._yadisk.remove(path)
                print(SUCCESSFUL_TRASH_MSG.format(file_name=path))
            else:
                print(ABORTED_MSG)

    def download(self, path, destination=None):
        requested_file_name = os.path.split(path)
        remote_file = self._yadisk.download(path)
        if not destination.endswith(os.path.sep):
            destination += os.path.sep
        if path.startswith("disk:/"):
            path.replace("disk:/", "")
        path_parts = path.split("/")
        #  rebuild path for platform independence
        if remote_file.name != requested_file_name:
            path_parts[-1] = remote_file.name
            print(DOWNLOADING_DIR_AS_ZIP_MSG.format(dir_name=path, file_name=remote_file.name))
        else:
            print(DOWNLOADING_FILE_MSG.format(file_name=remote_file.name))
        dl_path = os.path.join(destination, *path_parts)
        with open(dl_path, "wb+") as f:
            f.write(remote_file.data)
        print(SUCCESSFUL_DOWNLOAD_MSG.format(file_name=remote_file.name))

    @staticmethod
    def print(file):
        default_view = file.name + " " + f"({file.path})"
        if file.type == "dir":
            print("".join(Fore.CYAN + default_view + Style.RESET_ALL))
        else:
            print(default_view)
