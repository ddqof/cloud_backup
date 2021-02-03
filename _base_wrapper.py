import os

from abc import ABC, abstractmethod

from defaults import (
    OVERWRITING_DIRECTORY_MSG,
    OVERWRITING_FILE_MSG,
    OVERWRITE_FILE_REQUEST_MSG,
    OW_ACCESS_DENIED_MSG,
    RM_ACCESS_DENIED_MSG,
    UPLOADING_FILE_MSG,
    DELETE_DIR_CONFIRMATION_MSG,
    SUCCESSFUL_DELETE_FILE_MSG,
    MOVE_FILE_TO_TRASH_CONFIRMATION_MSG,
    SUCCESSFUL_FILE_TRASH_MSG,
    DELETE_FILE_CONFIRMATION_MSG,
    SUCCESSFUL_DELETE_DIR_MSG,
    MOVE_DIR_TO_TRASH_CONFIRMATION_MSG,
    SUCCESSFUL_DIR_TRASH_MSG,
    OVERWRITE_DIR_REQUEST_MSG,
)


class BaseWrapper(ABC):

    def __init__(self, storage):
        self._storage = storage

    @staticmethod
    def print_ow_dialog(path):
        if os.path.isfile(path):
            overwrite_confirm = OVERWRITE_FILE_REQUEST_MSG.format(file_name=path)
            exit_msg = OVERWRITING_FILE_MSG.format(file_name=path)
        else:
            overwrite_confirm = OVERWRITE_DIR_REQUEST_MSG.format(dir_name=path)
            exit_msg = OVERWRITING_DIRECTORY_MSG.format(dir_name=path)
        user_confirm = input(overwrite_confirm)
        if user_confirm in {"y", "yes", ""}:
            print(exit_msg)
        else:
            raise PermissionError(OW_ACCESS_DENIED_MSG)

    def put_file(self, local_path, destination):
        """
        Get upload link and then upload file raw binary data using this link.
        """
        link = self._storage.get_upload_link(local_path, destination)
        print(UPLOADING_FILE_MSG.format(file_name=local_path))
        with open(local_path, "rb") as f:
            file_data = f.read()
        self._storage.upload_file(link, file_data)

    def remove(
            self,
            file_id,
            permanently=False
    ) -> None:
        """
        Remove file or directory on GoogleDrive or YandexDisk storage.
        """
        file = self._storage.get_file(file_id)
        if permanently:
            if file.type == "dir":
                delete_confirm = DELETE_DIR_CONFIRMATION_MSG.format(
                    dir_name=file.name)
                exit_msg = SUCCESSFUL_DELETE_DIR_MSG.format(
                    dir_name=file.name)
            else:
                delete_confirm = DELETE_FILE_CONFIRMATION_MSG.format(
                    file_name=file.name)
                exit_msg = SUCCESSFUL_DELETE_FILE_MSG.format(
                    file_name=file.name)
        else:
            if file.type == "dir":
                delete_confirm = MOVE_DIR_TO_TRASH_CONFIRMATION_MSG.format(
                    dir_name=file.name)
                exit_msg = SUCCESSFUL_DIR_TRASH_MSG.format(
                    dir_name=file.name)
            else:
                delete_confirm = MOVE_FILE_TO_TRASH_CONFIRMATION_MSG.format(
                    file_name=file.name)
                exit_msg = SUCCESSFUL_FILE_TRASH_MSG.format(
                    file_name=file.name)
        user_confirm = input(delete_confirm)
        if user_confirm in {"y", "yes", ""}:
            self._storage.remove(file_id, permanently=permanently)
            print(exit_msg)
        else:
            raise PermissionError(RM_ACCESS_DENIED_MSG)

        @abstractmethod
        def download():
            ...

        @abstractmethod
        def lsdir():
            ...

        @abstractmethod
        def upload():
            ...
