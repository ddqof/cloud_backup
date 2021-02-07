import errno
import os

from _base_wrapper import BaseWrapper
from pathlib import PurePath, Path, PurePosixPath
from cloudbackup.yadisk import YaDisk
from defaults import (
    YADISK_SORT_KEYS,
    LIST_NEXT_PAGE_MSG,
)
from cli_msgs import YadiskDLMessage, ULMessage


class YaDiskWrapper(BaseWrapper):
    """
    Implements CLI interface to YandexDisk API.
    """

    def __init__(self):
        super().__init__(YaDisk())

    def lsdir(self, path, order_key) -> None:
        """
        Prints content of `path`. Prints all files
         excluding directories if path is None.
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
                print(file.str_value())
        else:
            page = self._storage.lsdir(
                path,
                offset=offset,
                sort=YADISK_SORT_KEYS[order_key]
            )
            while True:
                for file in page.files:
                    print(file.str_value())
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

    def upload(self, filename, destination) -> None:
        """
        Upload file located at `filename` to `destination`. Prints absolute
         file path while uploading because of '.' path.
        """
        file_path = Path(filename)
        if file_path.is_file():
            self._put_file(
                local_path=file_path,
                destination=PurePosixPath(destination, file_path.name)
            )
        elif file_path.is_dir():
            tree = os.walk(file_path)
            for root, dirs, filenames in tree:
                root_path = Path(root)
                target = PurePosixPath(destination, root_path)
                print(ULMessage(root).str_value())
                self._storage.mkdir(target)
                for filename in filenames:
                    self._put_file(
                        local_path=Path(root, filename),
                        destination=PurePosixPath(str(target), filename)
                    )
        else:
            raise FileNotFoundError(
                errno.ENOENT, os.strerror(errno.ENOENT), file_path)

    def download(self, file, local_destination, ov=False) -> None:
        """
        Download file on remote to local_destination.
        """
        p = PurePath(file.id)
        if local_destination is None:
            dl_path = PurePath(p.name)
        else:
            dl_path = PurePath(local_destination, p.name)
        if file.type == "dir":
            dl_path = dl_path.with_suffix(".zip")
        dl_path = Path(dl_path)
        print(YadiskDLMessage(dl_path, file.type, file.id, ov).str_value())
        download_link = self._storage.get_download_link(file.id)
        dl_path.write_bytes(self._storage.download(download_link))
