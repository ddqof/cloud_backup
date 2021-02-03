import errno
import os
import shutil

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

    def download(self, file_id, local_destination=None, overwrite=False) -> None:
        """
        Download file or directory by id of GDrive file.
        """
        file = self._storage.get_file(file_id)
        if local_destination is None:
            dl_path = file.name
        else:
            dl_path = os.path.join(local_destination, file.name)
        dl_path = os.path.abspath(dl_path)
        if overwrite and os.path.exists(dl_path):
            super().print_ow_dialog(dl_path)
        if not overwrite and os.path.exists(dl_path):
            raise FileExistsError(
                errno.EEXIST,
                os.strerror(errno.EEXIST),
                dl_path
            )
        else:
            if file.type == "file":
                print(DOWNLOADING_FILE_MSG.format(file_name=dl_path))
                file_bytes = self._storage.download(file.id)
                with open(dl_path, "wb+") as f:
                    f.write(file_bytes)
            elif file.type == "dir":
                if overwrite and os.path.exists(dl_path):
                    shutil.rmtree(dl_path)
                    os.mkdir(dl_path)
                else:
                    print(MAKING_DIRECTORY_MSG.format(dir_name=dl_path))
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
                                      overwrite=overwrite)
                    next_page_token = page.next_page_token
                    if next_page_token is None:
                        break
            else:
                print(SKIP_G_SUITE_FILE_MSG.format(file_name=dl_path))

    def upload(self, file_path, parents) -> None:
        """
        Upload file or directory by path.
        """
        file_abs_path = os.path.abspath(file_path)
        if os.path.isfile(file_abs_path):
            super().put_file(file_abs_path, parents)
        elif os.path.isdir(file_abs_path):
            parents = {}
            tree = os.walk(file_abs_path)
            for root, dirs, filenames in tree:
                if root.endswith(os.path.sep):
                    root = root[:-1]
                parent_id = parents[os.path.split(root)[0]] if parents else []
                dir_name = os.path.split(root)[-1]
                print(UPLOADING_DIRECTORY_MSG.format(dir_name=root))
                folder_id = self._storage.mkdir(dir_name,
                                                parent_id=parent_id)
                for file in filenames:
                    ul_path = os.path.join(root, file)
                    super().put_file(ul_path, folder_id)
                parents[root] = folder_id
        else:
            raise FileNotFoundError(
                errno.ENOENT,
                os.strerror(errno.ENOENT),
                file_path
            )
