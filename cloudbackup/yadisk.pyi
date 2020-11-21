from ._authenticators import YaDiskAuth as YaDiskAuth
from .exceptions import ApiResponseException as ApiResponseException, IncorrectPathException as IncorrectPathException
from ._file_objects import YaDiskFile as YaDiskFile
import requests


class YaDisk:
    _auth_headers: dict
    def __init__(self) -> None: ...
    def lsdir(self,
              directory: str,
              sort: str = ...,
              limit: int = ...,
    ) -> list: ...
    def list_files(self,
                   sort: str = ...,
                   limit: int = ...,
    ) -> list: ...
    def download(self,
                 path: str
    ) -> None: ...
    def upload(self,
               file_abs_path: str,
               destination: str
    ) -> None: ...
    def _initilal_upload(self,
                         destination: str
    ) -> str: ...
    def     _single_upload(self,
                       local_path: str,
                       destination: str
    ) -> None: ...
    def mkdir(self,
              destination: str
    ) -> None: ...
    @staticmethod
    def _check_path(path: str) -> None: ...
    @staticmethod
    def _check_status(api_response: requests.models.Response) -> None: ...