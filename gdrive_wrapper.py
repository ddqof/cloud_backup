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
from cloudbackup.file_objects import GDriveFile
from cloudbackup.gdrive import GDrive


class GDriveWrapper(BaseWrapper):
    """
    Implements CLI interface to Google Drive API
    """

    def __init__(self, gdrive: GDrive):
        super().__init__(gdrive)

    def lsdir(self, file_id, order_key) -> None:
        """
        Method allows to print each file in directory using `GDrive` class
        from `cloudbackup.gdrive`.

        Args:
            order_key: attribute used to sort the list of files.
        """
        if file_id is None:
            files = self.get_all_files(
                owners=['me'],
                order_by=GDRIVE_SORT_KEYS[order_key]
            )
            for file in files.values():
                print(file)
        else:
            page_token = None
            while True:
                page = self._storage.lsdir(
                    dir_id=file_id,
                    owners=['me'],
                    page_size=20,
                    order_by=GDRIVE_SORT_KEYS[order_key],
                    page_token=page_token)
                for file in page.files:
                    print(file)
                if page.next_page_token is not None:
                    user_confirm = input(LIST_NEXT_PAGE_MSG)
                    if user_confirm in {"y", "yes", ""}:
                        page_token = page.next_page_token
                        continue
                    else:
                        print(ABORTED_MSG)
                        break
                else:
                    break

    def download(self, file, local_destination=None, overwrite=False) -> None:
        """
        Method allows to download file or directory using `GDrive` class
        from `cloudbackup.gdrive`. Skips G.Suite files.

        Args:
            file: GDriveFileObject to download.
            local_destination: Optional; Pass path where to
             store downloaded file.
            overwrite: Optional; Whether to overwrite file if
             it already exists.

        Raises:
            ApiResponseException: an error occurred accessing API.
            ValueError: if user denied access to overwrite file or directory
            FileExistsError: if file exists but overwrite key wasn't given
        """
        if local_destination is None:
            dl_path = file.name
        else:
            dl_path = os.path.join(local_destination, file.name)
        dl_path = os.path.abspath(dl_path)
        if overwrite and os.path.exists(dl_path):
            print_ow_dialog(dl_path)
        if not overwrite and os.path.exists(dl_path):
            raise FileExistsError(
                errno.EEXIST,
                os.strerror(errno.EEXIST),
                dl_path
            )
        else:
            if file.type == "file":
                print(DOWNLOADING_FILE_MSG.format(file_name=dl_path))
                file_bytes = self._gdrive.download(file.id)
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
                    page = self._gdrive.lsdir(file.id,
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

    def get_all_files(self, owners=None, order_by="modifiedTime") -> dict:
        """
        Method used for getting all files on Google Drive storage using
        `GDrive` class from `cloudbackup.gdrive`.

        Args:
            owners: Optional; list of owners whose files should be listed.
            order_by: Optional; Sort key.

        Returns:
            A dict with the first 5 id symbols and GDriveFileObject matching.
            For example:

            {"123xy": GDriveFileObject_1,
             "xyzls": GDriveFileObject_2}
        """
        all_files, page_token = [], None
        while True:
            page_files, next_page_token = self._storage.lsdir(
                owners=owners,
                page_size=1000,
                order_by=order_by,
                page_token=page_token
            )
            all_files.extend(page_files)
            if next_page_token is None:
                break
            else:
                page_token = next_page_token
        files_with_id = {}
        for file in all_files:
            start_id = file.id[:5]
            files_with_id[start_id] = file
        return files_with_id

    def upload(self, file_path, parents) -> None:
        """
        Method allows to upload directories or files using `GDrive` class
        from `cloudbackup.gdrive`.

        Args:
            file_path: file path which need to be uploaded.
            parents: Optional; id of directory where file should
             be saved.

        Raises:
            FileNotFoundError: an error occurred accessing file
             using `file_abs_path`.
            ApiResponseException: an error occurred accessing API.
        """
        file_abs_path = os.path.abspath(file_path)
        if os.path.isfile(file_abs_path):
            super().upload(file_abs_path, parents)
        elif os.path.isdir(file_abs_path):
            parents = {}
            tree = os.walk(file_abs_path)
            for root, dirs, filenames in tree:
                if root.endswith(os.path.sep):
                    root = root[:-1]
                parent_id = parents[os.path.split(root)[0]] if parents else []
                # os.path.split returns pair (head, tail) of path
                dir_name = os.path.split(root)[-1]
                print(UPLOADING_DIRECTORY_MSG.format(dir_name=root))
                folder_id = self._storage.mkdir(dir_name,
                                                parent_id=parent_id)
                if not filenames:
                    continue
                for file in filenames:
                    ul_path = os.path.join(root, file)
                    super().upload(ul_path, folder_id)
                parents[root] = folder_id
        else:
            raise FileNotFoundError(
                errno.ENOENT,
                os.strerror(errno.ENOENT),
                file_path
            )
