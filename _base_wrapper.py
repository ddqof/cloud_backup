from abc import ABC, abstractmethod
from cli_msgs import DeleteConfirm, DeleteMessage
from defaults import RM_ACCESS_DENIED_MSG


class BaseWrapper(ABC):

    def __init__(self, storage):
        self._storage = storage

    def _put_file(self, local_path, destination):
        """
        Get upload link and then upload file raw binary data using this link.
        """
        link = self._storage.get_upload_link(local_path, destination)
        with open(local_path, "rb") as f:
            file_data = f.read()
        self._storage.upload_file(link, file_data)

    def remove(self, file_id, permanently=False) -> None:
        """
        Remove file or directory on GoogleDrive or YandexDisk storage.
        """
        file = self._storage.get_file(file_id)
        user_confirm = input(
            DeleteConfirm(file.name, permanently).str_value()
        )
        if user_confirm in {"y", "yes", ""}:
            self._storage.remove(file_id, permanently)
            print(DeleteMessage(file.name, permanently).str_value())
        else:
            raise PermissionError(RM_ACCESS_DENIED_MSG)

    def get_file(self, file_id):
        """
        Gets file meta-information by file_id.
        """
        return self._storage.get_file(file_id)

    @abstractmethod
    def download(self, file_id, local_destination, ov):
        ...

    @abstractmethod
    def lsdir(self, file_id, order_key):
        ...

    @abstractmethod
    def upload(self, file_id, destination):
        ...
