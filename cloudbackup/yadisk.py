import requests
from collections import namedtuple
from cloudbackup._authenticator import Authenticator
from cloudbackup.exceptions import (
    ApiResponseException,
    IncorrectPathException,
    FileIsNotDownloadableException
)
from cloudbackup.file_objects import YaDiskFile


class YaDisk:
    """
    Implements access to GoogleDrive API
    """

    def __init__(self):
        self._auth_headers = {
            "Content-Type": "application/json",
            "Authorization": Authenticator().get_yadisk_token()
        }

    def lsdir(
            self,
            path,
            sort="modified",
            limit=20,
            offset=0
    ) -> namedtuple("Page", ["file_info", "files"]):
        """
        Make request to get directory or file meta-information.

        Args:
            path: Directory to list. Examples: 'disk:/path/foo.py', '/path'.
            sort: Optional; Sort key. Valid keys are: 'name', 'path', 'size',
             'modified', 'created'. To sort in reversed order add a hyphen
              to the parameter value: '-name'.
            limit: Optional;The number of resources in the folder that should
             be described in the list.
            offset: Optional; The number of resources from the top of the list
             that should be skipped in the response
             (used for paginated output).

        Returns:
            |namedtuple| Page("dir_info", "files"). `dir_info` field contains
             meta-information of the file or directory itself. `files` contains
              list of `limit` size contains files of directory. If called
               for file instead of directory, `files` field  will be empty.

        Raises:
            ApiResponseException: an error occurred accessing API.
        """
        YaDisk._check_path(path)
        keys = {
            "path": path,
            "sort": sort,
            "limit": limit,
            "offset": offset,
        }
        r = requests.get(
            "https://cloud-api.yandex.net/v1/disk/resources/",
            params=keys,
            headers=self._auth_headers
        )
        if r.status_code != 200:
            raise ApiResponseException(
                r.status_code,
                r.json()["description"]
            )
        Page = namedtuple("Page", ["file_info", "files"])
        json_r = r.json()
        try:
            return Page(
                YaDiskFile(json_r),
                [YaDiskFile(file) for file in json_r["_embedded"]["items"]]
            )
        except KeyError:
            return Page(YaDiskFile(json_r), [])

    def list_files(self, sort="name", limit=20, offset=0) -> list:
        """
        Make request to get list of limited size consists of files on
         YandexDisk excluding directories.

        Args:
            sort: Sort key. Valid keys are: 'name', 'path', 'created',
             'modified', 'size'. To sort in reversed order add a hyphen
              to the parameter value: '-name'.
            limit: The number of resources in the folder that should be
             described in the list.
            offset: The number of resources from the top of the list that
            should be skipped in the response (used for paginated output).

        Returns:
            List of 'limit' size consists of YaDiskFileObjects represent each
             file excluding directories.
        """
        keys = {
            "sort": sort,
            "limit": limit,
            "offset": offset,
        }
        r = requests.get(
            "https://cloud-api.yandex.net/v1/disk/resources/files",
            params=keys,
            headers=self._auth_headers
        )
        if r.status_code != 200:
            raise ApiResponseException(
                r.status_code,
                r.json()["description"]
            )
        return [YaDiskFile(file) for file in r.json()["items"]]

    def get_download_link(self, path):
        YaDisk._check_path(path)
        request_for_link = requests.get(
            "https://cloud-api.yandex.net/v1/disk/resources/download",
            headers=self._auth_headers,
            params={"path": path}
        )
        if request_for_link.status_code != 200:
            raise ApiResponseException(
                request_for_link.status_code,
                request_for_link.json()["description"]
            )
        request_for_link = request_for_link.json()
        if not request_for_link["href"]:
            raise FileIsNotDownloadableException(path)
        return request_for_link["href"]

    def download(self, download_link) -> bytes:
        """
        Make a request for downloading file from YaDisk storage.

        Args:
            download_link: link from `get_download_link` method

        Returns:
            Raw bytes of downloaded file.

        Raises:
            ApiResponseException: an error occurred accessing API.
            FileIsNotDownloadable: an error occurred getting link for file with
             provided `path` argument.
        """
        download_request = requests.get(download_link)
        if download_request.status_code != 200:
            raise ApiResponseException(
                download_request.status_code,
                download_request.json()["description"]
            )
        return download_request.content

    def get_upload_link(self, destination) -> str:
        """
        Send initial request to get link for download a file.

        Args:
            destination: directory on YandexDisk storage where to
             save uploaded file. Examples: 'disk:/path/foo.py', '/path/bar'.

        Returns:
            URL for the file upload

        Raises:
            ApiResponseException: an error occurred accessing API.
        """
        YaDisk._check_path(destination)
        r = requests.get(
            "https://cloud-api.yandex.net/v1/disk/resources/upload",
            params={"path": destination},
            headers=self._auth_headers
        )
        if r.status_code != 200:
            raise ApiResponseException(r.status_code, r.json()["description"])
        return r.json()["href"]

    def upload_file(self, upload_link, file_data) -> None:
        """
        Upload a entire file by one single request. Before use
         this method call `get_upload_link` and provide upload
         link this method.

        Args:
            upload_link: link for uploading file
            file_data: raw binary file data

        Raises:
            ApiResponseException: an error occurred accessing API.
        """
        upload_request = requests.put(upload_link, data=file_data)
        if upload_request.status_code not in {201, 202}:
            raise ApiResponseException(
                upload_request.status_code,
                upload_request.json()["description"]
            )

    def mkdir(self, destination) -> None:
        """
        Make a request for making directory on YandexDisk storage.

        Args:
            destination: Path to folder which needs to be created.
             Examples: 'disk:/path/foo.py', '/path/bar'.

        Raises:
            ApiResponseException: an error occurred accessing API.
        """
        YaDisk._check_path(destination)
        path = {"path": destination}
        r = requests.put(
            "https://cloud-api.yandex.net/v1/disk/resources",
            params=path,
            headers=self._auth_headers
        )
        if r.status_code != 201:
            raise ApiResponseException(
                r.status_code,
                r.json()["description"]
            )

    def remove(self, path, permanently=False) -> None:
        """
        Make a request for removing file on YandexDisk storage.

        Args:
            path: Path to folder which needs to be deleted.
             Examples: 'disk:/path/foo.py', '/path/bar'.
            permanently: Optional; whether to delete the file
             permanently or move to the trash.

        Raises:
            ApiResponseException: an error occurred accessing API.
            IncorrectPathException: if path has prohibited chars.
        """

        YaDisk._check_path(path)
        flags = {
            "path": path,
            "permanently": permanently,
        }
        r = requests.request(
            "DELETE",
            "https://cloud-api.yandex.net/v1/disk/resources",
            params=flags,
            headers=self._auth_headers
        )
        if r.status_code not in {202, 204}:
            raise ApiResponseException(
                r.status_code,
                r.json()["description"]
            )

    @staticmethod
    def _check_path(path) -> None:
        """
        This method used for checking the path that will be specified in API
        request and raise exceptions if it's wrong.

        Params:
            path: path to a file on YaDisk storage.

        Raises:
            IncorrectPathException: if path has prohibited chars.
        """
        if not path.startswith("disk:/") and ":" in path:
            raise IncorrectPathException(path)
