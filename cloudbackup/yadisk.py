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
        Make request to get directory meta-information and return list of YaDiskFile objects.
        If directory isn't specified, return all files on YandexDisk storage
        :param directory: directory to list
        :return: list of YaDiskFile objects in
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

    def download(self, path):
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

    def upload(self, file_abs_path, destination):
        """
        Upload file to YandexDisk storage
        :param file_abs_path: absolute path of file
        :param destination: where to store uploaded file on YandexDisk
        :param multipart: use True if you want to upload safely, else set False
        :return: upload status message
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
            return "Upload completed"
        else:
            return "This directory or file doesn\'t exists"

    def _initilal_upload(self, destination):
        """
        Send inital request to get ref for download a file
        :param destination: directory on YandexDisk storage where to save uploaded file
        :return: URL for the file upload
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
        Make directory on YandexDisk storage.
        :param destination: path to created folder. You can provide like `disk:/path` or just `path`
        """
        YaDisk._check_path(destination)
        path = {"path": destination}
        r = requests.put("https://cloud-api.yandex.net/v1/disk/resources", params=path,
                         headers=self.auth_headers)
        if r.status_code != 201:
            raise ApiResponseException(r.status_code, r.json()["message"])

    @staticmethod
    def _check_path(path):
        if not path.startswith("disk") and ":" in path:
            raise IncorrectPathException(path)
