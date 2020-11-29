import errno
import os
import shutil
from colorama import Fore, Style
from defaults import (
    GDRIVE_SORT_KEYS,
    ABORTED_MSG,
    SUCCESSFUL_DELETE_FILE_MSG,
    SUCCESSFUL_FILE_TRASH_MSG,
    MOVE_TO_TRASH_CONFIRMATION_MSG,
    DELETE_CONFIRMATION_MSG,
    LIST_NEXT_PAGE_MSG,
    OVERWRITING_DIRECTORY_MSG,
    OVERWRITE_REQUEST_MSG,
    MAKING_DIRECTORY_MSG,
    DOWNLOADING_FILE_MSG,
    UPLOADING_FILE_MSG,
    UPLOADING_DIRECTORY_MSG,
    ACCESS_DENIED_MSG,
    OVERWRITING_FILE_MSG,
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

    def lsdir(self, file, order_key) -> None:
        """
        Method allows to print each file in directory using `GDrive` class
        from `cloudbackup.gdrive`.

        Args:
            file: `GDriveFileObject` which content needs to be listed.
            order_key: attribute used to sort the list of files.
        """
        if file is None:
            files = self.get_all_files(owners=['me'])
            for file in files:
                GDriveWrapper.print(file)
        else:
            if file.mime_type != "application/vnd.google-apps.folder":
                GDriveWrapper.print(file)
            else:
                while True:
                    page = self._gdrive.lsdir(dir_id=file.id, owners=['me'], page_size=20,
                                              order_by=GDRIVE_SORT_KEYS[order_key])
                    for file in page.files:
                        GDriveWrapper.print(file)
                    if page.next_page_token is not None:
                        user_confirm = input(LIST_NEXT_PAGE_MSG)
                        if user_confirm in {"y", "yes", ""}:
                            continue
                        else:
                            print(ABORTED_MSG)
                            break
                    else:
                        break

    def remove(self, file, permanently=False) -> None:
        """
        Method allows to remove file or directory using `GDrive` class
        from `cloudbackup.gdrive`.

        Args:
            file: GDriveFileObject to remove.
            permanently: Optional; whether to delete the file permanently or move to the trash.

        Raises:
            ApiResponseException: an error occurred accessing API.
        """
        if permanently:
            user_confirm = input(DELETE_CONFIRMATION_MSG.format(file_name=file.name))
            if user_confirm in {"y", "yes", ""}:
                self._gdrive.remove(file.id, permanently=True)
                print(SUCCESSFUL_DELETE_FILE_MSG.format(file_name=file.name))

            else:
                print(ABORTED_MSG)
        else:
            user_confirm = input(MOVE_TO_TRASH_CONFIRMATION_MSG.format(file_name=file.name))
            if user_confirm in {"y", "yes", ""}:
                self._gdrive.remove(file.id)
                print(SUCCESSFUL_FILE_TRASH_MSG.format(file_name=file.name))
            else:
                print(ABORTED_MSG)

    def download(self, file, destination=None, overwrite=False) -> None:
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
        if destination is None:
            dl_path = file.name
        else:
            dl_path = os.path.join(destination, file.name)
        dl_path = os.path.abspath(dl_path)
        if overwrite and os.path.exists(dl_path):
            user_confirm = input(OVERWRITE_REQUEST_MSG.format(file_name=dl_path))
            if user_confirm not in {"y", "yes", ""}:
                print(ABORTED_MSG)
                raise PermissionError(ACCESS_DENIED_MSG)
            if os.path.isfile(dl_path):
                print(OVERWRITING_FILE_MSG.format(file_name=dl_path))
            elif os.path.isdir(dl_path):
                print(OVERWRITING_DIRECTORY_MSG.format(dir_name=dl_path))
        if not overwrite and os.path.exists(dl_path):
            raise FileExistsError(errno.EEXIST, os.strerror(errno.EEXIST), dl_path)
        if not file.mime_type.startswith(G_SUITE_FILES_TYPE):
            file_bytes = self._gdrive.download(file.id)
            with open(dl_path, "wb+") as f:
                f.write(file_bytes)
        elif file.mime_type == GDRIVE_DIRECTORY_TYPE:
            if overwrite and os.path.exists(dl_path):
                shutil.rmtree(dl_path)
                os.mkdir(dl_path)
            else:
                print(MAKING_DIRECTORY_MSG.format(dir_name=dl_path))
                os.mkdir(dl_path)
            while True:
                next_page_token = None
                page = self._gdrive.lsdir(file.id, owners=['me'], page_token=next_page_token, page_size=1000)
                for file in page.files:
                    if not file.mime_type.startswith(G_SUITE_FILES_TYPE):
                        print(DOWNLOADING_FILE_MSG.format(file_name=os.path.join(dl_path, file.name)))
                    self.download(file, destination=dl_path, overwrite=overwrite)
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
            page_files, next_page_token = self._gdrive.lsdir(owners=owners, page_size=1000, page_token=page_token)
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
            self._put_file(file_abs_path)
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
                    self._put_file(ul_path, parent_id=folder_id)
                parents[root] = folder_id
        else:
            raise FileNotFoundError(errno.ENOENT, os.strerror(errno.ENOENT), file_path)

    def _put_file(self, file_path, parent_id=None) -> None:
        """
        Getting link for upload file and then uploading file raw binary data
        to this link.

        Args:
            file_path: path to file which needs to be uploaded
            parent_id: Optional; id of parent folder passed in `file_path`

        Raises:
            ApiResponseException: an error occurred accessing API
        """
        print(UPLOADING_FILE_MSG.format(file_name=file_path))
        link = self._gdrive.get_upload_link(file_path, parent_id)
        with open(file_path, "rb") as f:
            file_data = f.read()
        self._gdrive.upload_entire_file(link, file_data)

    @staticmethod
    def print(file):
        """
        Colorized print of GDriveFile object. Directories print in cyan color.
        Files' color doesn't change.

        Args:
            file: GDriveFile object which needs to be printed.
        """
        default_view = file.name + " " + f"({file.id})"
        if file.mime_type == "application/vnd.google-apps.folder":
            print("".join(Fore.CYAN + default_view + Style.RESET_ALL))
        else:
            print(default_view)
