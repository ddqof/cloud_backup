import json
import os
import mimetypes
import errno
import requests
from ._authenticators import GDriveAuth
from ._file_objects import GDriveFile
from .exceptions import ApiResponseException


class GDrive:
    """
    Implements access to GoogleDrive API
    """

    def __init__(self):
        self._auth_headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {GDriveAuth.authenticate()}"
        }

    def upload(self, file_abs_path=None, multipart=False) -> None:
        """
        Upload file to Google Drive storage
        :param file_abs_path: absolute file path
        :param multipart: use True if you want to upload safely, else set False
        :return: upload status message
        :raises:
                FileNotFoundError: an error occurred accessing file using :param: file_abs_path
                ApiResponseException: an error occurred accessing API
        """
        if multipart:
            upload = self._multipart_upload
        else:
            upload = self._single_upload
        if os.path.isfile(file_abs_path):
            upload(file_abs_path)
        elif os.path.isdir(file_abs_path):
            parents = {}
            tree = os.walk(file_abs_path)
            for root, dirs, filenames in tree:
                if root.endswith(os.path.sep):
                    root = root[:-1]
                parent_id = parents[os.path.split(root)[0]] if parents else []
                # os.path.split returns pair (head, tail) of path
                folder_id = self.mkdir(os.path.split(root)[-1],
                                       parent_id=parent_id)
                if not filenames:
                    continue
                for file in filenames:
                    upload(os.path.join(root, file), parent_id=folder_id)
                parents[root] = folder_id
        else:
            raise FileNotFoundError(errno.ENOENT, os.strerror(errno.ENOENT), file_abs_path)

    def download(self, file_id, path=None) -> None:
        """
        Download file from Google Drive storage and write its data to file
        :param file_id: name of file to download
        :param path: (optional) pass absolute path where to store downloaded file
        :raise: ApiResponseException: an error occurred accessing API
        """
        file_bytes, filename = self._download_file(request_file_id=file_id)
        if path is None:
            dl_path = filename
        else:
            dl_path = os.path.join(path, filename)
        with open(dl_path, "wb+") as f:
            f.write(file_bytes)

    def lsdir(self, dir_id=None, trashed=False) -> list:
        """
        :param trashed: whether to list files from the trash
        :param dir_id: id of parent directory
        :return: list of GDriveFile objects
        :raise: ApiResponseException: an error occurred accessing API
        """
        flags = {
            "q": f"trashed={trashed}" if not dir_id
            else f"trashed={trashed} and '{dir_id}' in parents"
        }
        r = requests.get("https://www.googleapis.com/drive/v3/files",
                         params=flags, headers=self._auth_headers)
        GDrive._check_status(r)
        return [GDriveFile(file) for file in r.json()["files"]]

    def autocomplete_id(self, start_id) -> None or str:
        """
        Return id that starts with given id
        :param start_id: start id
        :return: completed id
        :raise: ApiResponseException: an error occurred accessing API
        """
        if start_id is None or start_id == "root":
            return start_id
        for file in self.lsdir():
            if file.id.startswith(start_id):
                return file.id
        return None

    def mkdir(self, name, parent_id=None) -> str:
        """
        Create folder in Google Drive storage
        :param name: folder name
        :param parent_id: ids of parents of this folder
        :return: id of created folder
        :raise: ApiResponseException: an error occurred accessing API
        """
        metadata = {
            "name": name,
            "mimeType": "application/vnd.google-apps.folder",
            "parents": [parent_id] if parent_id else []
        }
        r = requests.post("https://www.googleapis.com/drive/v3/files",
                          headers=self._auth_headers, data=json.dumps(metadata))
        GDrive._check_status(r)
        return r.json()["id"]

    def _download_file(self, request_file_id=None) -> tuple:
        """
        :param request_file_id: file id to download
        :return: tuple: (raw bytes of downloaded file, filename)
        :raise: ApiResponseException: an error occurred accessing API
        """
        file_id = None
        filename = None
        for file in self.lsdir():
            if file.id == request_file_id:
                file_id = file.id
                filename = file.name
        file_data = {"alt": "media"}
        r = requests.get(f"https://www.googleapis.com/drive/v3/files/{file_id}",
                         params=file_data,
                         headers=self._auth_headers)
        GDrive._check_status(r)
        return r.content, filename

    def delete(self, file_id, permanently=False) -> None:
        """
        Permanently deletes  a filename by id.
        :param file_id: id of file that should be deleted
        :param permanently: (optional) whether to delete the file permanently or move to the trash
        :raise: ApiResponseException: an error occurred accessing API
        """
        if permanently:
            r = requests.request("DELETE", f"https://www.googleapis.com/drive/v3/files/{file_id}",
                                 headers=self._auth_headers)
        else:
            r = requests.post(f"https://www.googleapis.com/drive/v2/files/{file_id}/trash",
                              headers=self._auth_headers)
        GDrive._check_status(r)

    def _empty_trash(self) -> None:
        """
        Empty trash without ability to restore. Be careful!
        :raise ApiResponseException: an error occurred accessing API
        """
        r = requests.request("DELETE", "https://www.googleapis.com/drive/v3/files/trash",
                             headers=self._auth_headers)
        GDrive._check_status(r)

    def _send_initial_request(self, file_path, parent_id=None) -> requests.models.Response:
        """
        Send initial request to prepare API to receive further requests to upload
        :param file_path: absolute path to file for upload
        :param parent_id: (optional) id of parent folder passed in `file_path`
        :raise ApiResponseException: an error occurred accessing API
        :return: response from API
        """
        filename = os.path.basename(file_path)
        headers = {
            "X-Upload-Content-Type": mimetypes.guess_type(file_path)[0]
            # returns tuple (mimetype, encoding)
        }
        headers.update(self._auth_headers)
        metadata = {"name": filename}
        if parent_id is not None:
            metadata["parents"] = [parent_id]
        metadata = json.dumps(metadata)
        r = requests.post("https://www.googleapis.com/upload/drive/v3/files?uploadType=resumable",
                          headers=headers, data=metadata)
        GDrive._check_status(r)
        return r

    def _single_upload(self, file_path, parent_id=None) -> dict:
        """
        Perform file upload by one single request. Faster than multipart upload.
        :param file_path: absolute path to file for upload
        :param parent_id: (optional) id of parent folder passed in `file_path`
        :raise ApiResponseException: an error occurred accessing API
        :return response from API
        """
        response = self._send_initial_request(file_path, parent_id)
        resumable_uri = response.headers["location"]
        with open(file_path, "rb") as f:
            file_data = f.read()
        r = requests.put(resumable_uri, data=file_data,
                         headers=response.headers)
        GDrive._check_status(r)
        return r.json()

    def _multipart_upload(self, file_path, parent_id=None) -> None:
        """
        Perform file upload by few little requests. Slower than single upload,
        but suitable if you want to make progress bar for upload status.
        :param file_path: absolute path to file for upload
        :param parent_id: (optional) id of parent folder passed in `file_path`
        """
        file_size = os.path.getsize(file_path)
        response = self._send_initial_request(file_path, parent_id)
        CHUNK_SIZE = 256 * 1024
        headers = response.headers
        resumable_uri = headers["location"]
        uploaded_size = 0
        with open(file_path, "rb") as file:
            while uploaded_size < file_size:
                if CHUNK_SIZE > file_size:
                    CHUNK_SIZE = file_size
                if file_size - uploaded_size < CHUNK_SIZE:
                    CHUNK_SIZE = file_size - uploaded_size
                file_data = file.read(CHUNK_SIZE)
                headers["Content-Length"] = str(CHUNK_SIZE)
                headers[
                    "Content-Range"] = \
                    f"bytes {str(uploaded_size)}-{str(uploaded_size + CHUNK_SIZE - 1)}/{file_size}"
                r = requests.put(resumable_uri, data=file_data, headers=headers)
                uploaded_size += CHUNK_SIZE
                print(r.status_code)
                if r.status_code == 200:
                    break
                diff = int(r.headers["range"].split("-")[1]) + 1 - uploaded_size
                # range header looks like "bytes=0-n", where n - received bytes
                file.seek(diff, 1)  # second parameter means seek relative to the current position

    @staticmethod
    def _check_status(response) -> None:
        """
        Raise ApiResponseException if API request has unsuccessful status code
        :param response: response object from `requests` library
        """
        if response.status_code in {400, 401, 403, 404, 429, 500}:
            raise ApiResponseException(response.status_code, response.json()["error"]["message"])
