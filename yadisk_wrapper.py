import errno
import os
from defaults import (
    YADISK_SORT_KEYS,
    LIST_NEXT_PAGE_MSG,
    DOWNLOADING_FILE_MSG,
    UPLOADING_DIRECTORY_MSG,
    SUCCESSFUL_DOWNLOAD_FILE_MSG,
    DOWNLOADING_DIR_AS_ZIP_MSG,
    UNEXPECTED_VALUE_MSG
)
from cloudbackup.yadisk import YaDisk
import common_operations


class YaDiskWrapper:

    def __init__(self, yadisk: YaDisk):
        self._yadisk = yadisk

    def lsdir(self, path, order_key) -> None:
        """
        Method allows to print each file in directory using `YaDisk` class
        from `cloudbackup.yadisk`.

        Args:
            path: path of the file which content needs to be listed.
            order_key: attribute used to sort the list of files.
        """
        if path == "root":
            path = "/"
        offset = 0
        if path is None:
            limit, all_files = 1000, []
            while True:
                page_files = self._yadisk.list_files(limit=limit,
                                                     sort=YADISK_SORT_KEYS[order_key],
                                                     offset=offset)
                if page_files:
                    all_files.extend(page_files)
                    offset += limit
                else:
                    break
            for file in all_files:
                common_operations.print_remote_file(file_name=file.name,
                                                    file_id=file.path,
                                                    file_type=file.type)
        else:
            page = self._yadisk.lsdir(path,
                                      offset=offset,
                                      sort=YADISK_SORT_KEYS[order_key])
            while True:
                for file in page.files:
                    common_operations.print_remote_file(file_name=file.name,
                                                        file_id=file.path,
                                                        file_type=file.type)
                offset += 20
                page = self._yadisk.lsdir(path,
                                          offset=offset,
                                          sort=YADISK_SORT_KEYS[order_key])
                if not page.files:
                    break
                user_confirm = input(LIST_NEXT_PAGE_MSG)
                if user_confirm in {"y", "yes", ""}:
                    continue
                else:
                    break

    def upload(self, file_path, destination="/") -> None:
        """
        Method allows to download file or directory using `YaDisk` class
        from `cloudbackup.yadisk`.

        Args:
            file_abs_path: absolute path of file.
            destination: where to store uploaded file on YandexDisk.

        Raises:
            ApiResponseException: an error occurred accessing API.
        """
        if os.path.isfile(file_path):
            common_operations.put_file(
                storage=self._yadisk,
                local_path=file_path,
                destination=f"{destination}{os.path.split(file_path)[1]}")
        elif os.path.isdir(file_path):
            if file_path.endswith(os.path.sep):
                file_path = file_path[:-1]
            tree = os.walk(file_path)
            head = os.path.split(file_path)[0]
            for root, dirs, filenames in tree:
                destination = root.split(head)[1]
                print(UPLOADING_DIRECTORY_MSG.format(dir_name=destination))
                self._yadisk.mkdir(destination)
                if not filenames:
                    continue
                for filename in filenames:
                    current_ul_path = os.path.join(root, filename)
                    common_operations.put_file(storage=self._yadisk,
                                               local_path=current_ul_path,
                                               destination=f"{destination}/{filename}")
        else:
            raise FileNotFoundError(errno.ENOENT, os.strerror(errno.ENOENT), file_path)

    def remove(self, path, permanently=False) -> None:
        remote_file = self._yadisk.lsdir(path).file_info
        common_operations.remove(storage=self._yadisk,
                                 file_name=remote_file.name,
                                 destination=path,
                                 file_type=remote_file.type,
                                 permanently=permanently)

    def download(self, path, destination=None, overwrite=False) -> None:
        #  rebuild path for platform independence
        if path.startswith("disk:/"):
            path_chunks = path[5:].split("/")
        else:
            path_chunks = path.split("/")
        #  check if directory downloadable only as zip
        remote_file_object = self._yadisk.lsdir(path).file_info
        if remote_file_object.type == "dir":
            path_chunks[-1] = remote_file_object.name + ".zip"
        if destination is None:
            dl_path = path_chunks[-1]
        else:
            if not destination.endswith(os.path.sep):
                destination += os.path.sep
            dl_path = os.path.join(destination, path_chunks[-1])
        dl_path = os.path.abspath(dl_path)
        if remote_file_object.type == "dir":
            print(DOWNLOADING_DIR_AS_ZIP_MSG.format(dir_name=path, file_name=dl_path))
        elif remote_file_object.type == "file":
            print(DOWNLOADING_FILE_MSG.format(file_name=dl_path))
        else:
            raise ValueError(UNEXPECTED_VALUE_MSG.format(var_name=remote_file_object))
        if overwrite and os.path.exists(path):
            common_operations.print_overwrite_dialog(path)
        else:
            raise FileExistsError(errno.EEXIST, os.strerror(errno.EEXIST), dl_path)
        file_content = self._yadisk.download(path)
        with open(dl_path, "wb+") as f:
            f.write(file_content)
            print(SUCCESSFUL_DOWNLOAD_FILE_MSG.format(file_name=path_chunks[-1]))
