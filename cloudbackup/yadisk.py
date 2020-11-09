import json
import os
import mimetypes
import requests
from ._yadisk_authenticator import YaDiskAuth


class YaDisk:
    def __init__(self):
        self.auth_headers = {
            "Content-Type": "application/json",
            "Authorization": YaDiskAuth.authenticate()
        }
        self.all_files = self._get_files()

    def _get_files(self, path=None, trashed=False, list_all=False):
        """
        Process the raw response for file meta-information
        :param path:
        :param trashed:
        :param list_all:
        :return:
        """

        files = []
        if path is not None:
            r = requests.get("https://cloud-api.yandex.net/v1/disk/resources/", params={"path": path},
                             headers=self.auth_headers).json()
            files_list = r["_embedded"]["items"]
        else:
            r = requests.get("https://cloud-api.yandex.net/v1/disk/resources/files", headers=self.auth_headers).json()
            files_list = r["items"]
        for file_data in files_list:
            file = {}
            for key in file_data:
                if key == "name" or key == "path" or key == "type" or key == "mime_type":
                    file[key] = file_data[key]
                elif key == "resource_id":
                    file["id"] = file_data[key].split(":")[1]
                    # resource id is 115807909:3c36364d42da9c... where first part is not unique
            files.append(file)
        return files

    def list_files(self, folder_id=None) -> list:
        """
        Return list of dicts: {'name': '', 'id': '', 'path': '', 'type': '', 'mime_type': ''}
        'type' not equals 'mimeType', 'type' might be only 'dir' or 'file'
        """
        if folder_id == "" or folder_id is None:
            return self.all_files
        return self._get_files(path=folder_id)

    def _get_path_by_id(self):
        pass
