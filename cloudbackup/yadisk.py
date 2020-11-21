import os
import requests
from urllib.parse import parse_qs
from ._authenticators import YaDiskAuth
from .exceptions import ApiResponseException, IncorrectPathException
from ._file_objects import YaDiskFile


class YaDisk:
    """
    Implements access to GoogleDrive API
    """

    def __init__(self):
        self._auth_headers = {
            "Content-Type": "application/json",
            "Authorization": YaDiskAuth.authenticate()
        }

    def lsdir(self, directory, sort="modified", limit=20) -> list:
        """
        Make request to get directory meta-information list of limited size consists of
        inner files and directories.

        Args:
            directory: Directory to list. For example: "disk:/foo/photo2.png"
            sort: Sort key. Valid keys are: 'name', 'path', 'created', 'modified', 'size'.
              To sort in reversed order add a hyphen to the parameter value: '-name'.
            limit: The number of resources in the folder that should be described in the list.

        Returns:
            Yields list of 'limit' size consists of YaDiskFile objects represent each file and directory.

        Raises:
            ApiResponseException: an error occurred accessing API.
        """
        offset = 0
        keys = {
            "path": directory,
            "sort": sort,
            "limit": limit,
            "offset": offset,
        }
        while True:
            keys.update({"offset": offset})
            r = requests.get("https://cloud-api.yandex.net/v1/disk/resources/", params=keys,
                             headers=self._auth_headers)
            YaDisk._check_status(r)
            yield [YaDiskFile(file) for file in r.json()["_embedded"]["items"]]
            offset += limit
            if not r.json()["_embedded"]["items"]:
                return

    def list_files(self, sort="name", limit=20) -> list:
        """
        Make request to get list of limited size consists of files on YandexDisk excluding directories.

        Args:
            sort: Sort key. Valid keys are: 'name', 'path', 'created', 'modified', 'size'.
              To sort in reversed order add a hyphen to the parameter value: '-name'.
            limit: The number of resources in the folder that should be described in the list.

        Returns:
            Yields list of 'limit' size consists of YaDiskFileObjects represent each file excluding directories.
        """
        offset = 0
        keys = {
            "sort": sort,
            "limit": limit,
            "offset": offset,
        }
        while True:
            keys.update({"offset": offset})
            r = requests.get("https://cloud-api.yandex.net/v1/disk/resources/files", params=keys,
                             headers=self._auth_headers)
            YaDisk._check_status(r)
            yield [YaDiskFile(file) for file in r.json()["items"]]
            offset += limit
            if not r.json()["items"]:
                return

    def download(self, path) -> None:
        """
        Make a request for downloading file from YaDisk storage and
        then writing file's data to file.

        Args:
            path: File path which need to download.

        Raises:
            ApiResponseException: an error occurred accessing API.
        """
        YaDisk._check_path(path)
        r = requests.get("https://cloud-api.yandex.net/v1/disk/resources/download", headers=self._auth_headers,
                         params={"path": path})
        YaDisk._check_status(r)
        r = r.json()
        parsed_url = parse_qs(r["href"])  # returns queries like 'filename': ['test.zip']
        download_request = requests.get(r["href"])
        YaDisk._check_status(download_request)
        with open(parsed_url["filename"][0], "wb+") as f:
            f.write(download_request.content)

    def upload(self, file_abs_path, destination) -> None:
        """
        Upload file to YandexDisk storage

        Args:
            file_abs_path: absolute path of file.
            destination: where to store uploaded file on YandexDisk.

        Raises:
            ApiResponseException: an error occurred accessing API.
        """
        if os.path.isfile(file_abs_path):
            self._single_upload(file_abs_path, destination)
        elif os.path.isdir(file_abs_path):
            if file_abs_path.endswith(os.path.sep):
                file_abs_path = file_abs_path[:-1]
            tree = os.walk(file_abs_path)
            head = os.path.split(file_abs_path)[0]
            for root, dirs, filenames in tree:
                destination = root.split(head)[1]
                self.mkdir(destination)
                if not filenames:
                    continue
                for file in filenames:
                    self._single_upload(os.path.join(root, file), f"{destination}/{file}")

    def _initial_upload(self, destination) -> str:
        """
        Send inital request to get ref for download a file

        Args:
            destination: directory on YandexDisk storage where to save uploaded file

        Returns:
            URL for the file upload

        Raises:
            ApiResponseException: an error occurred accessing API.
        """
        r = requests.get("https://cloud-api.yandex.net/v1/disk/resources/upload", params={"path": destination},
                         headers=self._auth_headers)
        YaDisk._check_status(r)
        return r.json()["href"]

    def _single_upload(self, local_path, destination) -> None:
        YaDisk._check_path(destination)
        upload_ref = self._initilal_upload(destination)
        with open(local_path, "rb") as f:
            file_data = f.read()
        upload_request = requests.put(upload_ref, data=file_data)
        YaDisk._check_status(upload_request)

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
        YaDisk._check_status(r)

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
