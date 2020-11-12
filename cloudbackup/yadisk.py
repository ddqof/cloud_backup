import os
from urllib.parse import urlencode
import requests
from urllib.parse import parse_qs
from ._yadisk_authenticator import YaDiskAuth


class YaDisk:
    def __init__(self):
        self.auth_headers = {
            "Content-Type": "application/json",
            "Authorization": YaDiskAuth.authenticate()
        }
        self.all_files = self._get_files()

    def _get_files(self, path=None):
        """
        Process the raw response for file meta-information
        :param path:
        :param trashed:
        :param list_all:
        :return:
        """
        if path is not None:
            r = requests.get("https://cloud-api.yandex.net/v1/disk/resources/", params={"path": path},
                             headers=self.auth_headers).json()
            try:
                files_list = r["_embedded"]["items"]
            except KeyError:
                files_list = r
        else:
            r = requests.get("https://cloud-api.yandex.net/v1/disk/resources/files", headers=self.auth_headers).json()
            files_list = r["items"]
        return files_list

    def list_files(self, folder_id=None) -> list:
        """
        Return list of dicts: {'name': '', 'id': '', 'path': '', 'type': '', 'mime_type': ''}
        'type' not equals 'mimeType', 'type' might be only 'dir' or 'file'
        """
        files = []
        if folder_id == "" or folder_id is None:
            for file_data in self._get_files():
                file = {}
                for key in file_data:
                    if key == "name" or key == "path" or key == "type" or key == "mime_type":
                        file[key] = file_data[key]
                    elif key == "resource_id":
                        file["id"] = file_data[key].split(":")[1]
                        # resource id is 115807909:3c36364d42da9c... where first part is not unique
                files.append(file)
            return files
        return self._get_files(path=folder_id)

    def download(self, path):
        r = requests.get("https://cloud-api.yandex.net/v1/disk/resources/download", headers=self.auth_headers,
                         params={"path": path}).json()
        parsed_url = parse_qs(r["href"])  # returns queries like 'filename': ['test.zip']
        download_request = requests.get(r["href"])
        with open(parsed_url["filename"][0], "wb+") as f:
            f.write(download_request.content)

    def upload(self, file_abs_path, destination="/"):
        """
        Upload file to YandexDisk storage
        :param file_abs_path: absolute path of file
        :param destination: where to store uploaded file on YandexDisk
        :param multipart: use True if you want to upload safely, else set False
        :return: upload status message
        """
        if os.path.isfile(file_abs_path):
            destination = destination + os.path.split(file_abs_path)[1]
            self._single_upload(file_abs_path, destination)
        elif os.path.isdir(file_abs_path):
            if file_abs_path.endswith(os.path.sep):
                file_abs_path = file_abs_path[:-1]
            tree = os.walk(file_abs_path)
            head = os.path.split(file_abs_path)[0]
            for root, dirs, filenames in tree:
                destination = root.split(head)[1]
                self._create_folder(destination)
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
        :param path: path to download file
        :return: ref for downloading file
        """
        path = {"path": destination}
        r = requests.get("https://cloud-api.yandex.net/v1/disk/resources/upload", params=urlencode(path),
                         headers=self.auth_headers)
        print(r.text)
        return r.json()["href"]

    def _single_upload(self, local_path, destination):
        if destination is None:
            destination = os.path.split(local_path)[-1]
        ref = self._initilal_upload(destination)
        with open(local_path, "rb") as f:
            file_data = f.read()
        upload_request = requests.put(ref, data=file_data)

    def _create_folder(self, destination):
        """
        Create folder in YandexDisk storage
        :param destination: name of folder to create
        :return:
        """
        path = {"path": destination}
        r = requests.put("https://cloud-api.yandex.net/v1/disk/resources", params=path,
                         headers=self.auth_headers)
        print(r.status_code)

        # TODO: handle all possible errors
