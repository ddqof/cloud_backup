import errno
import os
import shutil
from colorama import Fore, Style
from defaults import (GDRIVE_SORT_KEYS,
                      ABORTED_MSG,
                      SUCCESSFUL_DELETE_MSG,
                      SUCCESSFUL_TRASH_MSG,
                      MOVE_TO_TRASH_CONFIRMATION_MSG,
                      DELETE_CONFIRMATION_MSG,
                      LIST_NEXT_PAGE_MSG,
                      OVERWRITING_DIRECTORY_MSG,
                      OVERWRITE_REQUEST_MSG,
                      MAKING_DIRECTORY_MSG,
                      DOWNLOADING_FILE_MSG,
                      UPLOADING_FILE_MSG,
                      UPLOADING_DIRECTORY_MSG)
from cloudbackup._file_objects import GDriveFile
from cloudbackup.gdrive import GDrive


class GDriveWrapper:

    def __init__(self, gdrive: GDrive):
        self._gdrive = gdrive

    def lsdir(self, file, order_key):
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

    def remove(self, file, permanently=False):
        if permanently:
            user_confirm = input(DELETE_CONFIRMATION_MSG.format(file_name=file.name))
            if user_confirm in {"y", "yes", ""}:
                self._gdrive.remove(file.id, permanently=True)
                print(SUCCESSFUL_DELETE_MSG.format(file_name=file.name))

            else:
                print(ABORTED_MSG)
        else:
            user_confirm = input(MOVE_TO_TRASH_CONFIRMATION_MSG.format(file_name=file.name))
            if user_confirm in {"y", "yes", ""}:
                self._gdrive.remove(file.id)
                print(SUCCESSFUL_TRASH_MSG.format(file_name=file.name))
            else:
                print(ABORTED_MSG)

    def download(self, file, destination=None, overwrite=False) -> None:
        """
        Download file from Google Drive storage and write its data to file.

        По дефолту скипает g_suite файлы.
        Args:
            file: GDriveFileObject to download.
            destination: Optional; pass absolute path where to store downloaded file.
            overwrite: Whether to overwrite file if it already exists.

        Raises:
            ApiResponseException: an error occurred accessing API.
        """
        if destination is None:
            dl_path = file.name
        else:
            dl_path = os.path.join(destination, file.name)
        if overwrite and os.path.exists:
            user_confirm = input(OVERWRITE_REQUEST_MSG.format(file_name=dl_path))
            if user_confirm not in {"y", "yes", ""}:
                print(ABORTED_MSG)
                return
        elif os.path.exists(dl_path):
            raise FileExistsError(errno.EEXIST, os.strerror(errno.EEXIST), dl_path)
        if not file.mime_type.startswith("application/vnd.google-apps"):
            file_bytes = self._gdrive.download(file.id)
            with open(dl_path, "wb+") as f:
                f.write(file_bytes)
        elif file.mime_type == "application/vnd.google-apps.folder":
            if overwrite and os.path.exists(dl_path):
                print(OVERWRITING_DIRECTORY_MSG.format(file_name=dl_path))
                shutil.rmtree(dl_path)
                os.mkdir(dl_path)
            else:
                print(MAKING_DIRECTORY_MSG.format(file_name=dl_path))
                os.mkdir(dl_path)
            while True:
                next_page_token = None
                page = self._gdrive.lsdir(file.id, owners=['me'], page_token=next_page_token, page_size=1000)
                for file in page.files:
                    print(DOWNLOADING_FILE_MSG.format(file_name=os.path.join(dl_path, file.name)))
                    self.download(file, destination=dl_path, overwrite=overwrite)
                next_page_token = page.next_page_token
                if next_page_token is None:
                    break

    def get_all_files(self, owners=None):
        all_files, page_token = [], None
        while True:
            page_files, next_page_token = self._gdrive.lsdir(owners=owners, page_size=1000, page_token=page_token)
            all_files.extend(page_files)
            if next_page_token is None:
                break
            else:
                page_token = next_page_token
        return all_files

    def get_file_object_by_id(self, start_id):
        """
        This method used for user-friendly CLI interface that allows
        type only start of full file id.

        Args:
            start_id: start of id
        Returns:
             GDriveFileObject that has id starts with given start_id
        """
        if start_id is None:
            raise ValueError("Id mustn't be a None")
        if start_id == "root":
            return GDriveFile({"name": "root", "id": "root", "mimeType": "application/vnd.google-apps.folder"})
        found = []
        for file in self.get_all_files():
            if file.id.startswith(start_id):
                found.append(file)
        if len(found) > 1:
            raise ValueError("Please enter more symbols to determine File ID.")
        elif len(found) == 1:
            return found[0]
        else:
            raise FileNotFoundError(f"There is no file starts with id: {start_id}.")

    def upload(self, file_abs_path, multipart=False) -> None:
        """
        Upload file to Google Drive storage

        Args:
            file_abs_path: absolute file path.
            multipart: use True if you want to upload safely, else set False.

        Raises:
            FileNotFoundError: an error occurred accessing file using `file_abs_path`.
            ApiResponseException: an error occurred accessing API.
        """
        if multipart:
            upload = self.multipart_upload
        else:
            upload = self.single_upload
        if os.path.isfile(file_abs_path):
            upload(file_abs_path)
        elif os.path.isdir(file_abs_path):
            parents = {}
            tree = os.walk(file_abs_path)
            for root, dirs, filenames in tree:
                if root.endswith(os.path.sep):
                    root = root[:-1]
                parent_id = parents[os.path.split(root)[0]] if parents else []
                # os.path.split returns pair (head, tail) of path
                dir_name = os.path.split(root)[-1]
                print(UPLOADING_DIRECTORY_MSG.format(file_name=root))
                folder_id = self._gdrive.mkdir(dir_name,
                                               parent_id=parent_id)
                if not filenames:
                    continue
                for file in filenames:
                    ul_path = os.path.join(root, file)
                    print(UPLOADING_FILE_MSG.format(file_name=ul_path))
                    upload(ul_path, parent_id=folder_id)
                parents[root] = folder_id
        else:
            raise FileNotFoundError(errno.ENOENT, os.strerror(errno.ENOENT), file_abs_path)

    def single_upload(self, file_path, parent_id=None):
        """
        Perform file upload by one single request. Faster than multipart upload.

        Args:
            file_path: absolute path to file for upload
            parent_id: (optional) id of parent folder passed in `file_path`

        Returns:
            A dict-like response from GoogleDrive API. For example:

            {'kind': 'drive#file', 'id': '1cqoEi5O1_UhplHXeTJXXXXXXXXa6rFfq',
             'name': 'test.txt', 'mimeType': 'text/plain'}

        Raises:
            ApiResponseException: an error occurred accessing API
        """
        link = self._gdrive.get_upload_link(file_path, parent_id)
        with open(file_path, "rb") as f:
            file_data = f.read()
        self._gdrive.upload_entire_file(link, file_data)

    def multipart_upload(self, file_path, parent_id=None) -> None:
        """
        Perform file upload by few little requests. Slower than single upload,
        but suitable if you want to make progress bar for upload status.

        Params:
            file_path: absolute path to file for upload
            parent_id: Optional; id of parent folder passed in `file_path`
        """
        file_size = os.path.getsize(file_path)
        resumable_uri = self._gdrive.send_file_info(file_path, parent_id)
        chunk_size = 256 * 1024
        uploaded_size = 0
        with open(file_path, "rb") as file:
            while uploaded_size < file_size:
                if chunk_size > file_size:
                    chunk_size = file_size
                if file_size - uploaded_size < chunk_size:
                    chunk_size = file_size - uploaded_size
                file_data = file.read(chunk_size)
                status = self._gdrive.upload_chunk(resumable_uri,
                                                   file_data=file_data,
                                                   uploaded_size=uploaded_size,
                                                   chunk_size=chunk_size,
                                                   file_size=file_size)
                uploaded_size += chunk_size
                print(status.code)
                if status.code == 200:
                    break
                diff = status.received - uploaded_size
                file.seek(diff, 1)  # second parameter means seek relative to the current position

    @staticmethod
    def print(file):
        default_view = file.name + " " + f"({file.id})"
        if file.mime_type == "application/vnd.google-apps.folder":
            print("".join(Fore.CYAN + default_view + Style.RESET_ALL))
        else:
            print(default_view)


