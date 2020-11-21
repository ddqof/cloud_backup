from ._authenticators import GDriveAuth as GDriveAuth
from .exceptions import ApiResponseException as ApiResponseException, RemoteFileNotFoundException as RemoteFileNotFoundException
from ._file_objects import GDriveFile as GDriveFile
import requests

class GDrive:
    _auth_headers: dict
    files: list
    def __init__(self) -> None: ...
    def upload(
            self,
            file_abs_path: str,
            multipart: bool = False
    ) -> None: ...
    def download(self,
                 file: GDriveFile,
                 path: str =...,
                 overwrite: bool = False,
    ) -> None: ...
    def lsdir(self,
              dir_id: str = ...,
              trashed: bool = False,
              owners: list = None,
              page_size: int = 20,
              order_by: str = "modifiedTime"
    ) -> list: ...
    def get_file_object_by_id(self,
                              start_id: str
    ) -> GDriveFile: ...
    def mkdir(self,
              name: str,
              parent_id: str = ...
    ) -> str: ...
    def remove(self,
               file_id: str,
               permanently: bool = False
    ) -> None: ...
    def _download_file(self,
                       file_id: str
    ) -> bytes: ...
    def _empty_trash(self) -> None: ...
    def _send_initial_request(self,
                              file_path: str,
                              parent_id: str = None
    ) -> requests.models.Response: ...
    def _single_upload(self,
                       file_path: str,
                       parent_id: str = None
    ) -> dict: ...
    def _multipart_upload(self,
                          file_path: str,
                          parent_id: str = None
    ) -> None: ...
    @staticmethod
    def _check_status(api_response: requests.models.Response) -> None: ...