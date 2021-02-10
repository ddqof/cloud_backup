import errno
import os
import shutil
from wrappers._base_wrapper import BaseWrapper
from cloudbackup.file_objects import GDriveFile
from defaults import (
    GDRIVE_SORT_KEYS,
    ABORTED_MSG,
    LIST_NEXT_PAGE_MSG,
)
from cloudbackup.gdrive import GDrive
from wrappers.cli_msgs import GdriveDLMessage, ULMessage
from pathlib import Path


class GDriveWrapper(BaseWrapper):
    """
    Implements CLI interface to Google Drive API
    """

    def __init__(self):
        super().__init__(GDrive())

    def lsdir(
            self,
            file_id: str,
            order_key: str
    ) -> None:
        """
        Prints content of directory or file itself. Prints all files
        if file_id is not provided. Otherwise prints files page by page.

        This method should properly call storage.lsdir method, print
        corresponding file info and if `file_id` is provided list files
        page by page by asking user before every next page.
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

    def download(
            self, file: GDriveFile,
            local_destination: Path,
            ov: bool = False
    ) -> None:
        """
        Download file or directory from GoogleDrive storage. This method
        should print what file or dir is being downloading, build
        correct download path, remove local file before download
        if ov=True and correctly call storage.download method (storage
        method takes care about `file` arg).
        """
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

    def upload(
            self,
            local_file: Path,
            parent_id: str
    ) -> None:
        """
        Upload file or directory by path. This method should print
        corresponding info about what file is uploading, determine
        what type of file is uploading and correctly calls
        storage.upload method.
        """
        if not local_file.name:
            local_file = local_file.resolve()
        print(ULMessage(local_file).str_value())
        if local_file.is_file():
            self._put_file(local_path=local_file, destination=parent_id)
        elif local_file.is_dir():
            folder_id = self._storage.mkdir(
                    local_file.name,
                    parent_id=parent_id
                )
            for child in local_file.iterdir():
                self.upload(child, folder_id)
        else:
            raise FileNotFoundError(
                errno.ENOENT, os.strerror(errno.ENOENT), local_file)
