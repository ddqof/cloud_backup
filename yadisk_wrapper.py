import errno
import os

from _base_wrapper import BaseWrapper
from pathlib import PurePath, Path, PurePosixPath
from cloudbackup.yadisk import YaDisk
from defaults import (
    YADISK_SORT_KEYS,
    LIST_NEXT_PAGE_MSG,
    DOWNLOADING_FILE_MSG,
    UPLOADING_DIRECTORY_MSG,
    DOWNLOADING_DIR_AS_ZIP_MSG,
)


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
                print(file)
        else:
            page = self._storage.lsdir(
                path,
                offset=offset,
                sort=YADISK_SORT_KEYS[order_key]
            )
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

    def upload(self, filename, destination) -> None:
        """
        Upload file located at `filename` to `destination`. Prints absolute
         file path while uploading because of '.' path.
        """
        file_path = Path(filename)
        if file_path.is_file():
            super().put_file(
                local_path=file_path,
                destination=PurePosixPath(destination, file_path.name)
            )
        elif file_path.is_dir():
            tree = os.walk(file_path)
            for root, dirs, filenames in tree:
                root_path = Path(root)
                target = PurePosixPath(destination, root_path)
                print(UPLOADING_DIRECTORY_MSG.format(dir_name=root))
                self._storage.mkdir(target)
                for filename in filenames:
                    super().put_file(
                        local_path=Path(root, filename),
                        destination=PurePosixPath(str(target), filename)
                    )
        else:
            raise FileNotFoundError(
                errno.ENOENT, os.strerror(errno.ENOENT), file_path)

    def download(self, file, local_destination=None, ov=False) -> None:
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
            download_msg = DOWNLOADING_DIR_AS_ZIP_MSG.format(
                dir_name=file.id, file_name=dl_path
            )
        else:
            download_msg = DOWNLOADING_FILE_MSG.format(file_name=dl_path)
        dl_path = Path(dl_path)
        if dl_path.exists():
            if ov:
                download_msg = super().get_ow_msg(dl_path)
            else:
                raise FileExistsError(
                    errno.EEXIST, os.strerror(errno.EEXIST), dl_path)
        print(download_msg)
        download_link = self._storage.get_download_link(file.id)
        dl_path.write_bytes(self._storage.download(download_link))
