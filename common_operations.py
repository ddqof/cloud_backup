import os

from colorama import Fore, Style

from defaults import (
    OVERWRITING_DIRECTORY_MSG,
    OVERWRITING_FILE_MSG,
    OVERWRITE_FILE_REQUEST_MSG,
    ABORTED_MSG,
    ACCESS_DENIED_MSG,
    UPLOADING_FILE_MSG,
    GDRIVE_DIRECTORY_TYPE,
    UNEXPECTED_VALUE_MSG,
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
from cloudbackup.gdrive import GDrive
from cloudbackup.yadisk import YaDisk


def print_overwrite_dialog(path) -> None:
    if os.path.isfile(path):
        overwrite_confirm = OVERWRITE_FILE_REQUEST_MSG.format(file_name=path)
        exit_msg = OVERWRITING_FILE_MSG.format(file_name=path)
    elif os.path.isdir(path):
        overwrite_confirm = OVERWRITE_DIR_REQUEST_MSG.format(dir_name=path)
        exit_msg = OVERWRITING_DIRECTORY_MSG.format(dir_name=path)
    else:
        raise ValueError(get_unexpected_value_msg(path))
    user_confirm = input(overwrite_confirm)
    if user_confirm in {"y", "yes", ""}:
        print(exit_msg)
    else:
        raise PermissionError(ACCESS_DENIED_MSG)


def remove(
        storage: GDrive or YaDisk,
        file_name,
        destination,
        file_type,
        permanently=False
) -> None:
    """
    Method allows to remove file or directory on YaDisk or Google Drive remote storage.

    Args:
        storage: storage where file needs to be deleted
        file_name: name of file on remote storage
        destination: id of file or folder that needs to be deleted in case of
         Google Drive. In case of YandexDisk storage remote file path is required.
        file_type: type of file on remote storage
        permanently: Optional; whether to delete the file permanently or move to the trash.

    Raises:
        ApiResponseException: an error occurred accessing API.
        IncorrectPathException: if remote file path has prohibited chars. In case of YaDisk storage only.
    """
    if isinstance(storage, (GDrive, YaDisk)):
        if permanently:
            if file_type in {"dir", GDRIVE_DIRECTORY_TYPE}:
                delete_confirm = DELETE_DIR_CONFIRMATION_MSG.format(dir_name=file_name)
                exit_msg = SUCCESSFUL_DELETE_DIR_MSG.format(dir_name=file_name)
            else:
                delete_confirm = DELETE_FILE_CONFIRMATION_MSG.format(file_name=file_name)
                exit_msg = SUCCESSFUL_DELETE_FILE_MSG.format(file_name=file_name)
        else:
            if file_type in {"dir", GDRIVE_DIRECTORY_TYPE}:
                delete_confirm = MOVE_DIR_TO_TRASH_CONFIRMATION_MSG.format(dir_name=file_name)
                exit_msg = SUCCESSFUL_DIR_TRASH_MSG.format(dir_name=file_name)
            else:
                delete_confirm = MOVE_FILE_TO_TRASH_CONFIRMATION_MSG.format(file_name=file_name)
                exit_msg = SUCCESSFUL_FILE_TRASH_MSG.format(file_name=file_name)
        user_confirm = input(delete_confirm)
        if user_confirm in {"y", "yes", ""}:
            storage.remove(destination, permanently=permanently)
        else:
            exit_msg = ABORTED_MSG
        print(exit_msg)
    else:
        raise ValueError(get_unexpected_value_msg(storage))


def put_file(storage: GDrive or YaDisk, local_path, destination=None) -> None:
    """
    Getting link for upload file and then uploading file raw binary data
    to this link.

    Args:
        storage: storage where to upload a file
        local_path: path to file which needs to be uploaded
        destination: id of parent folder in case of Google Drive or
         directory on YandexDisk storage where to save uploaded file.

    Raises:
        ApiResponseException: an error occurred accessing API
    """
    if isinstance(storage, GDrive):
        if destination is None:
            destination = "root"
        link = storage.get_upload_link(local_path, destination)
    elif isinstance(storage, YaDisk):
        if destination is None:
            destination = "/"
        link = storage.get_upload_link(destination)
    else:
        raise ValueError(get_unexpected_value_msg(storage))
    print(UPLOADING_FILE_MSG.format(file_name=local_path))
    with open(local_path, "rb") as f:
        file_data = f.read()
    storage.upload_file(link, file_data)


def print_remote_file(file_name, file_id, file_type) -> None:
    """
    Colorized print of file on remote storage. Directories print in cyan color.
    Files' color doesn't change.

    Args:
        file_name: name of file on remote storage
        file_type: type of file on remote storage
        file_id: file id on remote storage (e.g. path on YaDisk one or file id on GDrive)
    """

    default_view = f"{file_name} ({file_id})"
    if file_type in {"dir", GDRIVE_DIRECTORY_TYPE}:
        print("".join(Fore.CYAN + default_view + Style.RESET_ALL))
    else:
        print(default_view)


def get_unexpected_value_msg(variable):
    return UNEXPECTED_VALUE_MSG.format(
        #  check what returns f"{var=}", where var is a variable
        var_name=f"{variable=}".split("=")[0],
        value=variable,
    )
