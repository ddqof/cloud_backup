import errno
import os

from pathlib import PurePath, Path, PurePosixPath
from wrappers._base_wrapper import BaseWrapper
from cloudbackup.file_objects import YaDiskFile
from cloudbackup.yadisk import YaDisk
from defaults import (
    YADISK_SORT_KEYS,
    LIST_NEXT_PAGE_MSG,
)
from wrappers.cli_msgs import YadiskDLMessage, ULMessage


class YaDiskWrapper(BaseWrapper):
    """
    Implements CLI interface to YandexDisk API.
    """

    def __init__(self):
        super().__init__(YaDisk())

    def lsdir(
            self,
            path: str,
            order_key: str
    ) -> None:
        """
        Prints content of `path`. Prints all files
        excluding directories if path is None.
        Otherwise prints files page by page.
        """
        offset = 0
        while True:
            if path is None:
                limit = 1000
                files = self._storage.list_files(
                    limit=limit,
                    sort=YADISK_SORT_KEYS[order_key],
                    offset=offset
                )
            else:
                limit = 20
                files = self._storage.lsdir(
                    path,
                    limit=limit,
                    offset=offset,
                    sort=YADISK_SORT_KEYS[order_key]
                )
                next_page_is_not_empty = bool(
                    self._storage.lsdir(
                        path,
                        limit=limit,
                        offset=offset + limit,
                        sort=YADISK_SORT_KEYS[order_key])
                )
            offset += limit
            for file in files:
                print(file.str_value())
            if path is None and len(files) == limit:
                continue
            elif path is not None and next_page_is_not_empty:
                user_confirm = input(LIST_NEXT_PAGE_MSG)
                if user_confirm in {"y", "yes", ""}:
                    continue
                else:
                    break
            else:
                break

    def upload(
            self,
            local_file: Path,
            destination: str
    ) -> None:
        """
        Upload file located at `filename` to `destination`. Prints absolute
         file path while uploading because of '.' path.
        """
        if not local_file.name:
            local_file = local_file.resolve()
        if destination.startswith("disk:/"):
            normalized_dest = destination
        else:
            normalized_dest = "disk:" + destination
        print(ULMessage(local_file).str_value())
        normalized_dest = str(PurePosixPath(normalized_dest, local_file.name))
        if local_file.is_file():
            self._put_file(
                local_path=local_file,
                destination=normalized_dest
            )
        elif local_file.is_dir():
            self._storage.mkdir(normalized_dest)
            for child in local_file.iterdir():
                self.upload(child, normalized_dest)
        else:
            raise FileNotFoundError(
                errno.ENOENT, os.strerror(errno.ENOENT), local_file)

    def download(
            self, file: YaDiskFile,
            local_destination: Path,
            ov: bool = False
    ) -> None:
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
