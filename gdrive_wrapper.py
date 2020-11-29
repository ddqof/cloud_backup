import errno
import os
import shutil

import common_operations
from defaults import (
    GDRIVE_SORT_KEYS,
    ABORTED_MSG,
    LIST_NEXT_PAGE_MSG,
    MAKING_DIRECTORY_MSG,
    DOWNLOADING_FILE_MSG,
    UPLOADING_DIRECTORY_MSG,
    SKIP_G_SUITE_FILE_MSG,
    G_SUITE_FILES_TYPE,
    GDRIVE_DIRECTORY_TYPE
)
from cloudbackup.file_objects import GDriveFile
from cloudbackup.gdrive import GDrive


class GDriveWrapper:
    """
    Implements CLI interface to Google Drive API
    """

    def __init__(self, gdrive: GDrive):
        self._gdrive = gdrive

    def lsdir(self, start_id, order_key) -> None:
        """
        Method allows to print each file in directory using `GDrive` class
        from `cloudbackup.gdrive`.

        Args:
            file: `GDriveFileObject` which content needs to be listed.
            order_key: attribute used to sort the list of files.
        """
        file = self.get_file_object_by_id(start_id)
        if file is None:
            files = self.get_all_files(owners=['me'])
            for file in files:
                #  last argument shows whether file is directory or not
                common_operations.print_remote_file(
                    file_name=file.name,
                    file_id=file.id,
                    file_type=file.mime_type)
        else:
            if file.type != "dir":
                common_operations.print_remote_file(
                    file_name=file.name,
                    file_id=file.id,
                    file_type=file.type)
            else:
                while True:
                    page = self._gdrive.lsdir(dir_id=file.id,
                                              owners=['me'],
                                              page_size=20,
                                              order_by=GDRIVE_SORT_KEYS[order_key])
                    for file in page.files:
                        common_operations.print_remote_file(
                            file_name=file.name,
                            file_id=file.id,
                            file_type=file.mime_type)
                    if page.next_page_token is not None:
                        user_confirm = input(LIST_NEXT_PAGE_MSG)
                        if user_confirm in {"y", "yes", ""}:
                            continue
                        else:
                            print(ABORTED_MSG)
                            break
                    else:
                        break

    def remove(self, start_id, permanently=False) -> None:
        """
        Method allows to remove file or directory using `GDrive` class
        from `cloudbackup.gdrive`.

        Args:
            file: GDriveFileObject to remove.
            permanently: Optional; whether to delete the file permanently or move to the trash.

        Raises:
            ApiResponseException: an error occurred accessing API.
        """
        file = self.get_file_object_by_id(start_id)
        common_operations.remove(
            storage=self._gdrive,
            file_name=file.name,
            destination=file.id,
            file_type=file.type,
            permanently=permanently)

    def download(self, start_id, destination=None, overwrite=False) -> None:
        """
        Method allows to download file or directory using `GDrive` class
        from `cloudbackup.gdrive`. Skips G.Suite files.

        Args:
            file: GDriveFileObject to download.
            destination: Optional; Pass path where to store downloaded file.
            overwrite: Optional; Whether to overwrite file if it already exists.

        Raises:
            ApiResponseException: an error occurred accessing API.
            ValueError: if user denied access to overwrite file or directory
            FileExistsError: if file exists but overwrite key wasn't given
        """
        file = self.get_file_object_by_id(start_id)
        if destination is None:
            dl_path = file.name
        else:
            dl_path = os.path.join(destination, file.name)
        if overwrite and os.path.exists(dl_path):
            common_operations.print_overwrite_dialog(dl_path)
        if not overwrite and os.path.exists(dl_path):
            raise FileExistsError(errno.EEXIST, os.strerror(errno.EEXIST), dl_path)
        if not file.type == "file":
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
            while True:
                next_page_token = None
                page = self._gdrive.lsdir(file.id,
                                          owners=['me'],
                                          page_token=next_page_token,
                                          page_size=1000)
                for file in page.files:
                    if not file.mime_type.startswith(G_SUITE_FILES_TYPE):
                        print(DOWNLOADING_FILE_MSG.format(file_name=os.path.join(dl_path, file.name)))
                    self.download(file,
                                  destination=dl_path,
                                  overwrite=overwrite)
                next_page_token = page.next_page_token
                if next_page_token is None:
                    break
        else:
            print(SKIP_G_SUITE_FILE_MSG.format(file_name=dl_path))

    def get_all_files(self, owners=None) -> list:
        """
        Method used for getting all files on Google Drive storage using
        `GDrive` class from `cloudbackup.gdrive`.

        Args:
            owners: Optional; list of owners whose files should be listed.

        Returns:
            list of all files in Google Drive storage.
        """
        all_files, page_token = [], None
        while True:
            page_files, next_page_token = self._gdrive.lsdir(owners=owners,
                                                             page_size=1000,
                                                             page_token=page_token)
            all_files.extend(page_files)
            if next_page_token is None:
                break
            else:
                page_token = next_page_token
        return all_files

    def get_file_object_by_id(self, start_id) -> GDriveFile:
        """
        Method used for user-friendly CLI interface that allows
        type only start of file id to get full file id.

        Args:
            start_id: start of id
        Returns:
             GDriveFileObject that has id starts with given start_id
        """
        if start_id == "root":
            return GDriveFile({"name": "root", "id": "root", "mimeType": "application/vnd.google-apps.folder"})
        found = []
        for file in self.get_all_files():
            if file.id.startswith(start_id):
                found.append(file)
                if len(found) > 1:
                    raise FileNotFoundError("Please enter more symbols to determine File ID.")
        if len(found) == 1:
            return found[0]
        else:
            raise FileNotFoundError(f"There is no file starts with id: {start_id}.")

    def upload(self, file_path) -> None:
        """
        Method allows to upload directories or files using `GDrive` class
        from `cloudbackup.gdrive`.

        Args:
            file_path: file path.

        Raises:
            FileNotFoundError: an error occurred accessing file using `file_abs_path`.
            ApiResponseException: an error occurred accessing API.
        """
        file_abs_path = os.path.abspath(file_path)
        if os.path.isfile(file_abs_path):
            common_operations.put_file(
                storage=self._gdrive,
                local_path=file_abs_path)
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
                folder_id = self._gdrive.mkdir(dir_name,
                                               parent_id=parent_id)
                if not filenames:
                    continue
                for file in filenames:
                    ul_path = os.path.join(root, file)
                    common_operations.put_file(
                        storage=self._gdrive,
                        local_path=ul_path,
                        destination=folder_id)
                parents[root] = folder_id
        else:
            raise FileNotFoundError(errno.ENOENT,
                                    os.strerror(errno.ENOENT),
                                    file_path)
