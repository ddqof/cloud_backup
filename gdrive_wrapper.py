import errno
import os
import shutil
from _base_wrapper import BaseWrapper
from defaults import (
    GDRIVE_SORT_KEYS,
    ABORTED_MSG,
    LIST_NEXT_PAGE_MSG,
)
from cloudbackup.gdrive import GDrive
from cli_msgs import GdriveDLMessage, ULMessage
from pathlib import PurePath, Path


class GDriveWrapper(BaseWrapper):
    """
    Implements CLI interface to Google Drive API
    """

    def __init__(self):
        super().__init__(GDrive())

    def lsdir(self, file_id, order_key) -> None:
        """
        Prints content of directory or file itself. Prints all files
         if file_id is not provided. Otherwise prints files page by page.
        """
        page_token = None
        if file_id is None:
            page_size = 1000
        else:
            page_size = 20
        while True:
            page = self._storage.lsdir(
                dir_id=file_id,
                owners=['me'],
                page_size=page_size,
                order_by=GDRIVE_SORT_KEYS[order_key],
                page_token=page_token)
            for file in page.files:
                print(file.str_value())
            if page.next_page_token is not None:
                page_token = page.next_page_token
                if file_id is None:
                    continue
                user_confirm = input(LIST_NEXT_PAGE_MSG)
                if user_confirm in {"y", "yes", ""}:
                    continue
                else:
                    print(ABORTED_MSG)
                    break
            else:
                break

    def download(self, file, local_destination, ov=False) -> None:
        """
        Download file or directory from GoogleDrive storage.
        """
        if local_destination is None:
            dl_path = Path(file.name)
        else:
            dl_path = Path(local_destination, file.name)
        print(GdriveDLMessage(dl_path, file.type, ov).str_value())
        if dl_path.is_dir() and ov:
            shutil.rmtree(dl_path)
        elif dl_path.is_file() and ov:
            dl_path.unlink()
        elif dl_path.exists() and not ov:
            raise FileExistsError(
                errno.EEXIST, os.strerror(errno.EEXIST), dl_path)
        if file.type == "file":
            dl_path.write_bytes(self._storage.download(file.id))
        elif file.type == "dir":
            dl_path.mkdir()
            next_page_token = None
            while True:
                page = self._storage.lsdir(
                    file.id,
                    owners=['me'],
                    page_token=next_page_token,
                    page_size=1000
                )
                for file in page.files:
                    self.download(file, local_destination=dl_path, ov=ov)
                next_page_token = page.next_page_token
                if next_page_token is None:
                    break

    def upload(self, filename, parents) -> None:
        """
        Upload file or directory by path.

        P.S. os.walk returns root, dirs and filenames in not
        alphabetic order so it is hard to test it behaviour of
        this method. Due to this I use sorted(filenames) only for
        better testing.
        """
        file_path = Path(filename)
        if not file_path.name:
            file_path = file_path.resolve()
        if file_path.is_file():
            print(ULMessage(file_path).str_value())
            self._put_file(local_path=file_path, destination=parents)
        elif file_path.is_dir():
            parents = {}
            tree = os.walk(file_path)
            for root, dirs, filenames in tree:
                root_path = PurePath(root)
                parent_id = parents[root_path.parent] if parents else None
                print(ULMessage(root).str_value())
                folder_id = self._storage.mkdir(
                    root_path.name,
                    parent_id=parent_id
                )
                for file in sorted(filenames):
                    dest = Path(root, file)
                    print(ULMessage(dest).str_value())
                    self._put_file(local_path=dest, destination=folder_id)
                parents[root_path] = folder_id
        else:
            raise FileNotFoundError(
                errno.ENOENT, os.strerror(errno.ENOENT), filename)
