import errno
import os
import shutil
from pathlib import PurePath, Path

from _base_wrapper import BaseWrapper

from defaults import (
    GDRIVE_SORT_KEYS,
    ABORTED_MSG,
    LIST_NEXT_PAGE_MSG,
    MAKING_DIRECTORY_MSG,
    DOWNLOADING_FILE_MSG,
    UPLOADING_DIRECTORY_MSG,
    SKIP_G_SUITE_FILE_MSG,
)
from cloudbackup.gdrive import GDrive


class GDriveWrapper(BaseWrapper):
    """
    Implements CLI interface to Google Drive API
    """

    def __init__(self):
        super().__init__(GDrive())

    def lsdir(self, file_id, order_key="modifiedTime") -> None:
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
                print(file)
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

    def download(self, file, local_destination=None, ov=False) -> None:
        """
        Download file or directory by id of GDrive file.
        """
        if local_destination is None:
            dl_path = file.name
        else:
            dl_path = PurePath(local_destination, file.name)
        dl_path = Path(dl_path).resolve()
        if file.type == "file":
            dl_msg = DOWNLOADING_FILE_MSG.format(file_name=dl_path)
        elif file.type == "dir":
            dl_msg = MAKING_DIRECTORY_MSG.format(dir_name=dl_path)
        else:
            dl_msg = SKIP_G_SUITE_FILE_MSG.format(file_name=dl_path)
        if dl_path.exists():
            if ov:
                dl_msg = super().get_ow_msg(dl_path)
            else:
                raise FileExistsError(
                    errno.EEXIST,
                    os.strerror(errno.EEXIST),
                    dl_path
                )
        else:
            print(dl_msg)
            if file.type == "file":
                file_bytes = self._storage.download(file.id)
                dl_path.write_bytes(file_bytes)
            elif file.type == "dir":
                if dl_path.exists():
                    shutil.rmtree(dl_path)
                os.mkdir(dl_path)
                next_page_token = None
                while True:
                    page = self._storage.lsdir(file.id,
                                               owners=['me'],
                                               page_token=next_page_token,
                                               page_size=1000)
                    for file in page.files:
                        self.download(file,
                                      local_destination=dl_path,
                                      ov=ov)
                    next_page_token = page.next_page_token
                    if next_page_token is None:
                        break

    def upload(self, file_path, parents) -> None:
        """
        Upload file or directory by path.
        """
        p = Path(file_path).resolve()
        if p.is_file():
            super().put_file(p, parents)
        elif p.is_dir():
            parents = {}
            tree = os.walk(p)
            for root, dirs, filenames in tree:
                root_path = Path(root)
                parent_id = parents[root_path.parent] if parents else None
                print(UPLOADING_DIRECTORY_MSG.format(dir_name=root))
                folder_id = self._storage.mkdir(root_path.name,
                                                parent_id=parent_id)
                for file in filenames:
                    ul_path = PurePath(root, file)
                    super().put_file(ul_path, folder_id)
                parents[root] = folder_id
        else:
            raise FileNotFoundError(
                errno.ENOENT,
                os.strerror(errno.ENOENT),
                file_path
            )
