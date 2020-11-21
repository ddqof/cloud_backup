import json
import os
import mimetypes
import errno
import requests
import shutil
from ._authenticators import GDriveAuth
from ._file_objects import GDriveFile
from .exceptions import ApiResponseException, RemoteFileNotFoundException


class GDrive:
    """
    Implements access to GoogleDrive API.
    """

    def __init__(self):
        self._auth_headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {GDriveAuth.authenticate()}"
        }
        self.files = []
        for page in self.lsdir(owners=['me'], page_size=1000):
            self.files.extend(page)

    def upload(self, file_abs_path, multipart=False) -> None:
        """
        Upload file to Google Drive storage

        Args:
            file_abs_path: absolute file path.
            multipart: use True if you want to upload safely, else set False.

        Raises:
            FileNotFoundError: an error occurred accessing file using `file_abs_path`.
            ApiResponseException: an error occurred accessing API.
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

    def download(self, file, path=None, overwrite=False) -> None:
        """
        Download file from Google Drive storage and write its data to file.

        Args:
            file: GDriveFileObject to download.
            path: Optional; pass absolute path where to store downloaded file.
            overwrite: Whether to overwrite file if it already exists.

        Raises:
            ApiResponseException: an error occurred accessing API.
        """
        if path is None:
            dl_path = file.name
        else:
            dl_path = os.path.join(path, file.name)
        if file.mime_type != "application/vnd.google-apps.folder":
            file_bytes = self._download_file(file.id)
            if not overwrite and os.path.exists(dl_path):
                raise FileExistsError
            else:
                with open(dl_path, "wb+") as f:
                    f.write(file_bytes)
        else:
            if overwrite and os.path.exists:
                shutil.rmtree(dl_path)
                os.mkdir(dl_path)
            else:
                os.mkdir(dl_path)
            for page in self.lsdir(file.id, owners=['me'], page_size=1000):
                for file in page:
                    self.download(file, dl_path)

    def _download_file(self, file_id) -> bytes:
        """
        Make request for downloading file from GoogleDrive storage

        Args:
            file_id: file id to download

        Returns:
            Raw bytes of downloaded file`

        Raises:
            ApiResponseException: an error occurred accessing API
        """
        file_data = {"alt": "media"}
        r = requests.get(f"https://www.googleapis.com/drive/v3/files/{file_id}",
                         params=file_data,
                         headers=self._auth_headers)
        GDrive._check_status(r)
        return r.content

    def lsdir(self, dir_id=None, trashed=False, owners=None, page_size=20, order_by="modifiedTime") -> list:
        """
        Make request to get list of `page_size` size consists of files and directories in
        directory with specified dir_id.

        Args:
            order_by: Sort key. Valid keys are: 'createdTime', 'folder' (folders will show first in the list),
              'modifiedTime', 'name', 'recency', 'viewedByMeTime'. Each key sorts ascending by default,
               but may be reversed with the 'desc' modifier.
            dir_id: If None then list all files, else list files in a directory with given id
            trashed: Whether to list files from the trash
            owners: List or files owners
            page_size: Files count on one page (set value from 1 to 1000)

        Returns:
            Yield list of `page_size` consists of GDriveFile objects

        Raises:
            ApiResponseException: an error occurred accessing API
        """
        next_page_token = None
        if not dir_id:
            if owners:
                query = f"trashed={trashed} and '{','.join(owners)}' in owners"
            else:
                query = f"trashed={trashed}"
        else:
            if owners:
                query = f"trashed={trashed} and '{dir_id}' in parents and '{','.join(owners)}' in owners"
            else:
                query = f"trashed={trashed} and '{dir_id}' in parents"
        flags = {
            "q": query,
            "pageSize": page_size,
            "orderBy": order_by,
            "fields": "files(name, mimeType, parents, id), nextPageToken",
        }
        while True:
            if next_page_token is not None:
                flags.update({"pageToken": next_page_token})
            r = requests.get("https://www.googleapis.com/drive/v3/files",
                             params=flags, headers=self._auth_headers)
            GDrive._check_status(r)
            r = r.json()
            yield [GDriveFile(file) for file in r["files"]]
            try:
                next_page_token = r["nextPageToken"]
            except KeyError:
                return

    def get_file_object_by_id(self, start_id) -> GDriveFile:
        """
        This method used for user-friendly CLI interface that allows
        type only start of full file id.

        Args:
            start_id: start of id
        Returns:
             GDriveFileObject that has id starts with given start_id
        """
        for file in self.files:
            try:
                if file.id.startswith(start_id):
                    return file
            except TypeError:
                raise RemoteFileNotFoundException(start_id)

    def mkdir(self, name, parent_id=None) -> str:
        """
        Create a new directory in Google Drive storage.

        Params:
            name: Directory name.
            parent_id: Parent id of this folder.

        Returns:
            Id of created folder

        Raises:
            ApiResponseException: an error occurred accessing API
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

    def remove(self, file_id, permanently=False) -> None:
        """
        Method allows to remove permanently or move file to trash.

        Args:
            file_id: id of file that should be deleted.
            permanently: Optional; whether to delete the file permanently or move to the trash.

        Raises:
            ApiResponseException: an error occurred accessing API.
        """
        if permanently:
            r = requests.request("DELETE", f"https://www.googleapis.com/drive/v3/files/{file_id}")
        else:
            r = requests.post(f"https://www.googleapis.com/drive/v2/files/{file_id}/trash",
                              headers=self._auth_headers)
        GDrive._check_status(r)

    def _empty_trash(self) -> None:
        """
        Permanently deletes all files in the trash.

        Raises:
            ApiResponseException: an error occurred accessing API.
        """
        r = requests.request("DELETE", "https://www.googleapis.com/drive/v3/files/trash",
                             headers=self._auth_headers)
        GDrive._check_status(r)

    def _send_initial_request(self, file_path, parent_id=None) -> requests.models.Response:
        """
        Send initial request to prepare API to receive further requests to upload

        Args:
            file_path: absolute path to file for upload
            parent_id: (optional) id of parent folder passed in `file_path`

        Returns:
            A response object from `requests` library that has 'Location' header
            that specifies the resumable session URI for upload file.

        Raises:
             ApiResponseException: an error occurred accessing API
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

        Args:
            file_path: absolute path to file for upload
            parent_id: (optional) id of parent folder passed in `file_path`

        Returns:
            A dict-like response from GoogleDrive API. For example:

            {'kind': 'drive#file', 'id': '1cqoEi5O1_UhplHXeTJXXXXXXXXa6rFfq',
             'name': 'test.txt', 'mimeType': 'text/plain'}

        Raises:
            ApiResponseException: an error occurred accessing API
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

        Params:
            file_path: absolute path to file for upload
            parent_id: Optional; id of parent folder passed in `file_path`
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
    def _check_status(api_response) -> None:
        """
        This method used for checking the response status code after every API query.

        Params:
            api_response: response object from `requests` library.

        Raises:
            ApiResponseException: If API response has unsuccessful status code.
        """
        if api_response.status_code in {400, 401, 403, 404, 429, 500}:
            raise ApiResponseException(api_response.status_code, api_response.json()["error"]["message"])
