import json
import os
import mimetypes
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

    def get_path_by_id(self, id):
        for file in self.all_files:
            for metainf in file:
                if file[metainf].startswith(id):
                    return file["path"]

    def download(self, path):
        r = requests.get("https://cloud-api.yandex.net/v1/disk/resources/download", headers=self.auth_headers,
                         params={"path": path}).json()
        parsed_url = parse_qs(r["href"])  # returns queries like 'filename': ['test.zip']
        download_request = requests.get(r["href"])
        with open(parsed_url["filename"][0], "wb+") as f:
            f.write(download_request.content)
