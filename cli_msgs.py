import errno
import os
from pathlib import Path

from defaults import (
    OVERWRITING_FILE_MSG,
    OVERWRITE_FILE_REQUEST_MSG,
    OVERWRITE_DIR_REQUEST_MSG,
    OVERWRITING_DIRECTORY_MSG,
    OW_ACCESS_DENIED_MSG,
    SKIP_G_SUITE_FILE_MSG,
    MAKING_DIRECTORY_MSG,
    DOWNLOADING_FILE_MSG,
    UPLOADING_DIRECTORY_MSG,
    DOWNLOADING_DIR_AS_ZIP_MSG
)


class OVMessage:

    def __init__(self, path: Path):
        self._path = path

    def __str__(self):
        if self._path.is_file():
            ov_confirm = OVERWRITE_FILE_REQUEST_MSG.format(self._path)
            exit_msg = OVERWRITING_FILE_MSG.format(self._path)
        else:
            ov_confirm = OVERWRITE_DIR_REQUEST_MSG.format(self._path)
            exit_msg = OVERWRITING_DIRECTORY_MSG.format(self._path)
        user_confirm = input(ov_confirm)
        if user_confirm in {"y", "yes", ""}:
            return exit_msg
        else:
            raise PermissionError(OW_ACCESS_DENIED_MSG)


class DLMessage:

    def __init__(self, path: Path, file_type: str, ov: bool):
        self._path = path
        self._file_type = file_type
        self._ov = ov


class GdriveDLMessage(DLMessage):

    def __init__(self, path: Path, file_type: str, ov: bool):
        super().__init__(path, file_type, ov)

    def __str__(self):
        if self._file_type == "file":
            msg = DOWNLOADING_FILE_MSG.format(self._path)
        elif self._file_type == "dir":
            msg = MAKING_DIRECTORY_MSG.format(self._path)
        else:
            msg = SKIP_G_SUITE_FILE_MSG.format(self._path)
        if self._path.exists():
            if self._ov:
                msg = str(OVMessage(self._path))
            else:
                raise FileExistsError(
                    errno.EEXIST, os.strerror(errno.EEXIST), self._path)
        return msg


class YadiskDLMessage(DLMessage):

    def __init__(self, path: Path, file_type: str, file_id: str, ov: bool):
        super().__init__(path, file_type, ov)
        self._file_id = file_id

    def __str__(self):
        if self._file_type == "dir":
            msg = DOWNLOADING_DIR_AS_ZIP_MSG.format(
                self._file_id, self._path
            )
        else:
            msg = DOWNLOADING_FILE_MSG.format(self._path)
        if self._path.exists():
            if self._ov:
                msg = OVMessage(self._path)
            else:
                raise FileExistsError(
                    errno.EEXIST, os.strerror(errno.EEXIST), self._path)
        return msg


class ULMessage:

    def __init__(self, path):
        self._path = path

    def __str__(self):
        return UPLOADING_DIRECTORY_MSG.format(self._path)
