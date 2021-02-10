import errno
import os
from pathlib import Path
from wrappers.defaults import (
    OVERWRITE_REQUEST_MSG,
    OVERWRITING_MSG,
    OW_ACCESS_DENIED_MSG,
    SKIPPING_MSG,
    DOWNLOADING_MSG,
    UPLOADING_MSG,
    DOWNLOADING_AS_ZIP_MSG,
    SUCCESSFUL_DELETE_MSG,
    SUCCESSFUL_TRASH_MSG,
    DELETE_CONFIRMATION_MSG,
    MOVE_TO_TRASH_CONFIRMATION_MSG
)


class OVMessage:

    def __init__(self, path: Path):
        self._path = path

    def str_value(self):
        user_confirm = input(
            OVERWRITE_REQUEST_MSG.format(f"{self._path}")
        )
        if user_confirm in {"y", "yes", ""}:
            return OVERWRITING_MSG.format(f"{self._path}")
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

    def str_value(self):
        if self._file_type == "g.suite":
            msg = SKIPPING_MSG
        else:
            msg = DOWNLOADING_MSG
        if self._path.exists() and self._ov:
            msg = OVMessage(self._path).str_value()
        return msg.format(self._path)


class YadiskDLMessage(DLMessage):

    def __init__(self, path: Path, file_type: str, file_id: str, ov: bool):
        super().__init__(path, file_type, ov)
        self._file_id = file_id

    def str_value(self):
        if self._file_type == "dir":
            msg = DOWNLOADING_AS_ZIP_MSG.format(
                self._file_id, self._path
            )
        else:
            msg = DOWNLOADING_MSG.format(self._path)
        if self._path.exists():
            if self._ov:
                msg = OVMessage(self._path).str_value()
            else:
                raise FileExistsError(
                    errno.EEXIST, os.strerror(errno.EEXIST), str(self._path))
        return msg


class ULMessage:

    def __init__(self, path: Path):
        self._path = path

    def str_value(self):
        return UPLOADING_MSG.format(self._path)


class DeleteConfirm:

    def __init__(self, file_name: str, permanently: bool):
        self._file_name = file_name
        self._permanently = permanently

    def str_value(self):
        if self._permanently:
            msg = DELETE_CONFIRMATION_MSG
        else:
            msg = MOVE_TO_TRASH_CONFIRMATION_MSG
        return msg.format(self._file_name)


class DeleteMessage:

    def __init__(self, file_name: str, permanently: bool):
        self._file_name = file_name
        self._permanently = permanently

    def str_value(self):
        if self._permanently:
            msg = SUCCESSFUL_DELETE_MSG
        else:
            msg = SUCCESSFUL_TRASH_MSG
        return msg.format(self._file_name)
