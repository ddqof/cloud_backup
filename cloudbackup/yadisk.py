from collections import namedtuple

import requests
from urllib.parse import parse_qs
from cloudbackup._authenticators import YaDiskAuth
from cloudbackup.exceptions import ApiResponseException, IncorrectPathException, FileIsNotDownloadableException
from cloudbackup.file_objects import YaDiskFile


class YaDisk:
    """
    Implements access to GoogleDrive API
    """

    def __init__(self):
        self._auth_headers = {
            "Content-Type": "application/json",
            "Authorization": YaDiskAuth.authenticate()
        }

    def lsdir(self, directory, sort="modified", limit=20, offset=0):
        """
        Make request to get directory meta-information list of limited size consists of
        inner files and directories.

        Args:
            directory: Directory to list. For example: "disk:/foo/photo2.png"
            sort: Sort key. Valid keys are: 'name', 'path', 'created', 'modified', 'size'.
              To sort in reversed order add a hyphen to the parameter value: '-name'.
            limit: The number of resources in the folder that should be described in the list.

        Returns:
            List of 'limit' size consists of YaDiskFile objects represent each file and directory.

        Raises:
            ApiResponseException: an error occurred accessing API.
        """
        keys = {
            "path": directory,
            "sort": sort,
            "limit": limit,
            "offset": offset,
        }
        r = requests.get("https://cloud-api.yandex.net/v1/disk/resources/", params=keys,
                         headers=self._auth_headers)
        if r.status_code not in {200}:
            raise ApiResponseException(r.status_code, r.json()["description"])
        Page = namedtuple("Page", ["dir_info", "files"])
        json_r = r.json()
        try:
            return Page(YaDiskFile(json_r), [YaDiskFile(file) for file in json_r["_embedded"]["items"]])
        except KeyError:
            return Page(YaDiskFile(json_r), [])

    def list_files(self, sort="name", limit=20, offset=0) -> list:
        """
        Make request to get list of limited size consists of files on YandexDisk excluding directories.

        Args:
            sort: Sort key. Valid keys are: 'name', 'path', 'created', 'modified', 'size'.
              To sort in reversed order add a hyphen to the parameter value: '-name'.
            limit: The number of resources in the folder that should be described in the list.

        Returns:
            Yields list of 'limit' size consists of YaDiskFileObjects represent each file excluding directories.
        """
        keys = {
            "sort": sort,
            "limit": limit,
            "offset": offset,
        }
        r = requests.get("https://cloud-api.yandex.net/v1/disk/resources/files", params=keys,
                         headers=self._auth_headers)
        if r.status_code not in {200}:
            raise ApiResponseException(r.status_code, r.json()["description"])
        return [YaDiskFile(file) for file in r.json()["items"]]

    def download(self, path):
        """
        Make a request for downloading file from YaDisk storage and
        then writing file's data to file.

        Args:
            path: File path which need to download.

        Raises:
            ApiResponseException: an error occurred accessing API.
        """
        YaDisk._check_path(path)
        request_for_link = requests.get("https://cloud-api.yandex.net/v1/disk/resources/download",
                                        headers=self._auth_headers,
                                        params={"path": path})
        if request_for_link.status_code not in {200}:
            raise ApiResponseException(request_for_link.status_code, request_for_link.json()["description"])
        request_for_link = request_for_link.json()
        if request_for_link["href"] == "":
            raise FileIsNotDownloadableException(path)
        download_request = requests.get(request_for_link["href"])
        if download_request.status_code not in {200}:
            raise ApiResponseException(download_request.status_code, download_request.json()["description"])
        return download_request.content

    def _get_upload_link(self, destination) -> str:
        """
        Send initial request to get ref for download a file

        Args:
            destination: directory on YandexDisk storage where to save uploaded file

        Returns:
            URL for the file upload

        Raises:
            ApiResponseException: an error occurred accessing API.
        """
        r = requests.get("https://cloud-api.yandex.net/v1/disk/resources/upload",
                         params={"path": destination},
                         headers=self._auth_headers)
        if r.status_code not in {200}:
            raise ApiResponseException(r.status_code, r.json()["description"])
        return r.json()["href"]


    def single_upload(self, local_path, destination) -> None:
        YaDisk._check_path(destination)
        upload_ref = self._get_upload_link(destination)
        with open(local_path, "rb") as f:
            file_data = f.read()
        upload_request = requests.put(upload_ref, data=file_data)
        if upload_request.status_code not in {201, 202}:
            raise ApiResponseException(upload_request.status_code, upload_request.json()["description"])

    def mkdir(self, destination) -> None:
        """
        Create a request for making directory on YandexDisk storage.

        Args:
            destination: Path to created folder. Examples: 'disk:/path/foo.py', '/path/bar'.
        """
        YaDisk._check_path(destination)
        path = {"path": destination}
        r = requests.put("https://cloud-api.yandex.net/v1/disk/resources", params=path,
                         headers=self._auth_headers)
        if r.status_code not in {201}:
            raise ApiResponseException(r.status_code, r.json()["description"])

    def remove(self, path, permanently=False):
        YaDisk._check_path(path)
        flags = {
            "path": path,
            "permanently": permanently,
        }
        r = requests.request("DELETE", "https://cloud-api.yandex.net/v1/disk/resources",
                             params=flags,
                             headers=self._auth_headers)
        if r.status_code not in {202, 204}:
            raise ApiResponseException(r.status_code, r.json()["description"])

    @staticmethod
    def _check_path(path) -> None:
        """
        This method used for checking the path that will be specified in API
        request and raise exceptions if it's wrong.

        Params:
            path: path to a file on YaDisk storage

        Raises:
            IncorrectPathException: if path has prohibited chars.
        """
        if not path.startswith("disk") and ":" in path:
            raise IncorrectPathException(path)

    @staticmethod
    def _check_status(api_response) -> None:
        """
        This method used for checking the response status code after every API query.

        Params:
            api_response: response object from `requests` library.

        Raises:
            ApiResponseException: if API response has unsuccessful status code.
        """
        if api_response.status_code not in {200, 201}:
            raise ApiResponseException(api_response.status_code, api_response.json()["description"])
