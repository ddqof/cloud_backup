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
        self.auth_headers = {
            "Content-Type": "application/json",
            "Authorization": YaDiskAuth.authenticate()
        }

    def lsdir(self, directory=None) -> list:
        """
        Make request to get directory meta-information.

        Args:
            directory: Directory to list. For example: "disk:/foo/photo2.png"

        Returns:
            If directory isn't specified, return list of all files on YandexDisk storage (excluding directories
            due to YandexDisk API specific). If specified, returns list of all files and directories in this
            directory.

        Raises:
            ApiResponseException: an error occurred accessing API.
        """
        if directory is None:
            r = requests.get("https://cloud-api.yandex.net/v1/disk/resources/files", headers=self.auth_headers)
        else:
            r = requests.get("https://cloud-api.yandex.net/v1/disk/resources/", params={"path": directory},
                             headers=self.auth_headers)
        if r.status_code != 200:
            raise ApiResponseException(r.status_code, r.json()["message"])
        r = r.json()
        if "_embedded" in r:
            raw_files = r["_embedded"]["items"]
        elif "items" in r:
            raw_files = r["items"]
        else:
            raw_files = [r]
        return [YaDiskFile(file) for file in raw_files]

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
        r = requests.get("https://cloud-api.yandex.net/v1/disk/resources/download", headers=self.auth_headers,
                         params={"path": path})
        if r.status_code != 200:
            raise ApiResponseException(r.status_code, r.json()["message"])
        r = r.json()
        parsed_url = parse_qs(r["href"])  # returns queries like 'filename': ['test.zip']
        download_request = requests.get(r["href"])
        with open(parsed_url["filename"][0], "wb+") as f:
            f.write(download_request.content)

    def upload(self, file_abs_path, destination) -> None:
        """
        Upload file to YandexDisk storage

        Args:
            file_abs_path: absolute path of file.
            destination: where to store uploaded file on YandexDisk.
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

    def _initilal_upload(self, destination) -> str:
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
                         headers=self.auth_headers)
        if r.status_code != 200:
            raise ApiResponseException(r.status_code, r.json()["message"])
        return r.json()["href"]

    def _single_upload(self, local_path, destination):
        YaDisk._check_path(destination)
        upload_ref = self._initilal_upload(destination)
        with open(local_path, "rb") as f:
            file_data = f.read()
        upload_request = requests.put(upload_ref, data=file_data)
        if upload_request.status_code != 201:
            raise ApiResponseException(upload_request.status_code, upload_request.json()["message"])

    def mkdir(self, destination):
        """
        Create a request for making directory on YandexDisk storage.

        Args:
            destination: Path to created folder. Examples: 'disk:/path/foo.py', '/path/bar'.
        """
        YaDisk._check_path(destination)
        path = {"path": destination}
        r = requests.put("https://cloud-api.yandex.net/v1/disk/resources", params=path,
                         headers=self.auth_headers)
        if r.status_code != 201:
            raise ApiResponseException(r.status_code, r.json()["message"])

    @staticmethod
    def _check_path(path):
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
