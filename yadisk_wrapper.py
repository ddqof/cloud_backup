import errno
import os
import platform

from _base_wrapper import BaseWrapper
from pathlib import PurePath, Path, PureWindowsPath
from cloudbackup.yadisk import YaDisk
from defaults import (
    YADISK_SORT_KEYS,
    LIST_NEXT_PAGE_MSG,
    DOWNLOADING_FILE_MSG,
    UPLOADING_DIRECTORY_MSG,
    DOWNLOADING_DIR_AS_ZIP_MSG, UNEXPECTED_VALUE_MSG,
)


class YaDiskWrapper(BaseWrapper):
    """
    Implements CLI interface to YandexDisk API.
    """

    def __init__(self):
        super().__init__(YaDisk())

    def lsdir(self, path, order_key) -> None:
        """
        Prints content of directory or file itself. Prints all files
         excluding directories if path is not provided.
         Otherwise prints files page by page.
        """
        offset = 0
        if path is None:
            limit, all_files = 1000, []
            while True:
                page_files = self._storage.list_files(
                    limit=limit,
                    sort=YADISK_SORT_KEYS[order_key],
                    offset=offset
                )
                if page_files:
                    all_files.extend(page_files)
                    offset += limit
                else:
                    break
            for file in all_files:
                print(file)
        else:
            page = self._storage.lsdir(path,
                                       offset=offset,
                                       sort=YADISK_SORT_KEYS[order_key])
            while True:
                for file in page.files:
                    print(file)
                offset += 20
                page = self._storage.lsdir(
                    path,
                    offset=offset,
                    sort=YADISK_SORT_KEYS[order_key]
                )
                if not page.files:
                    break
                user_confirm = input(LIST_NEXT_PAGE_MSG)
                if user_confirm in {"y", "yes", ""}:
                    continue
                else:
                    break

    def upload(self, file_path, destination) -> None:
        """
        Upload file located at file_path to destination. Prints absolute
         file path while uploading because of '.' path.
        """
        if destination.endswith("/"):
            destination = destination[:-1]
        abs_file_path = os.path.abspath(file_path)
        if os.path.isfile(abs_file_path):
            super().put_file(
                abs_file_path,
                f"{destination}/{os.path.basename(file_path)}"
            )
        elif os.path.isdir(abs_file_path):
            if abs_file_path.endswith(os.path.sep):
                abs_file_path = abs_file_path[:-1]
            posix_base = os.path.dirname(YaDiskWrapper._get_posix_path(abs_file_path))
            tree = os.walk(abs_file_path)
            for root, dirs, filenames in tree:
                current_dir = root.replace(posix_base, "")
                target = f"{destination}{current_dir}"
                print(UPLOADING_DIRECTORY_MSG.format(dir_name=root))
                self._storage.mkdir(target)
                if not filenames:
                    continue
                for filename in filenames:
                    current_ul_path = os.path.join(root, filename)
                    super().put_file(
                        current_ul_path,
                        f"{target}/{filename}"
                    )
        else:
            raise FileNotFoundError(
                errno.ENOENT,
                os.strerror(errno.ENOENT),
                abs_file_path)

    @staticmethod
    def _get_posix_path(path):
        """
        Get posix path by any other path. Used for platform independence.
        """
        if platform.system() in {"Darwin", "Linux"}:
            return path
        elif platform.system() == "Windows":
            return PureWindowsPath(path).as_posix()
        else:
            raise ValueError

    def download(self, file, local_destination=None, ov=False) -> None:
        """
        Download file on remote to local_destination.
        """
        p = PurePath(file.id)
        if local_destination is None:
            dl_path = p.name
        else:
            dl_path = PurePath(local_destination, p.name)
        if file.type == "dir":
            dl_path = dl_path.with_suffix(".zip")
            download_msg = DOWNLOADING_DIR_AS_ZIP_MSG.format(
                dir_name=file.id, file_name=dl_path
            )
        else:
            download_msg = DOWNLOADING_FILE_MSG.format(file_name=dl_path)
        if Path(dl_path).exists():
            if ov:
                download_msg = super().get_ow_msg(dl_path)
            else:
                raise FileExistsError(
                    errno.EEXIST,
                    os.strerror(errno.EEXIST),
                    dl_path
                )
        else:
            print(download_msg)
            download_link = self._storage.get_download_link(file.id)
            with open(dl_path, "wb+") as f:
                f.write(self._storage.download(download_link))
