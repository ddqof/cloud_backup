import json
import os
import mimetypes
import requests
from cloudbackup._gdrive_authenticator import GDriveAuth


class GDrive:
    def __init__(self):
        self._auth_headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {GDriveAuth.authenticate()}"
        }
        self.all_files = self._get_files(list_all=True)

    def upload(self, file_abs_path=None, multipart=True):
        """
        Upload file to Google Drive storage
        :param file_abs_path: absolute path of file
        :param multipart: use True if you want to upload safely, else set False
        :return: upload status message
        """
        if multipart:
            upload = self._multipart_upload
        else:
            upload = self._single_upload
        tree = os.walk(file_abs_path)
        if os.path.isfile(file_abs_path):
            upload(file_abs_path)
        elif os.path.isdir(file_abs_path):
            parents = {}
            for root, dirs, filenames in tree:
                if root.endswith(os.path.sep):
                    root = root[:-1]
                parent_id = parents[os.path.split(root)[0]] if parents else []
                # os.path.split returns pair (head, tail) of path
                folder_id = self._create_folder(os.path.split(root)[-1],
                                                parent_id=parent_id)
                if not filenames:
                    continue
                for file in filenames:
                    upload(os.path.join(root, file), parent_id=folder_id)
                parents[root] = folder_id
            return "Upload completed"
        else:
            return "This directory or file doesn\'t exists"

    def download(self, file_id, path=None):
        """
        Download file from Google Drive storage
        :param file_id: name of file to download
        :param path: (optional) pass absolute path where you want to store downloaded file
        :return: status message
        """
        try:
            file_bytes, filename = self._download_file(request_file_id=file_id)
        except FileNotFoundError:
            return f"File: starts with `{file_id}` id not found"
        if path is None:
            dl_path = filename
            path = "present working"
        else:
            dl_path = os.path.join(path, filename)
        with open(dl_path, "wb+") as f:
            f.write(file_bytes)
            return f"Successfully download file: {filename} to {path} directory"

    def list_files(self, folder_id=None):
        """
        Return dict: {'kind': '', 'id': '', 'name': '', 'mimeType': ''}
        """
        if folder_id == "" or folder_id is None:
            return self.all_files
        return self._get_files(parent_id=folder_id)

    def autocomplete_id(self, id):
        """
        Return id that starts with given id
        :param id: start id
        :return: completed id
        """
        if id is None or id == "root":
            return id
        for file in self.all_files:
            if file["id"].startswith(id):
                return file["id"]
        return None

    def _create_folder(self, name, parent_id=None):
        """
        Create folder in Google Drive storage
        :param name: folder name
        :param parent_id: ids of parents of this folder
        :return: id of created folder
        """
        metadata = {
            "name": name,
            "mimeType": "application/vnd.google-apps.folder",
            "parents": [parent_id] if parent_id else []
        }
        r = requests.post("https://www.googleapis.com/drive/v3/files",
                          headers=self._auth_headers, data=json.dumps(metadata))
        return r.json()["id"]

    def _get_files(self, parent_id=None, trashed=False, list_all=False):
        """
        Return list of files on Google Drive storage
        :param trashed: whether to show files that are in the trash
        :param list_all: whether to list all files and directories on storage
        :return: JSON file that includes files info
        """
        flags = {
            "q": f"trashed={trashed}" if list_all
            else f"trashed={trashed} and '{parent_id}' in parents"
        }
        json_r = requests.get("https://www.googleapis.com/drive/v3/files",
                              params=flags, headers=self._auth_headers).json()
        return json_r["files"]

    def _download_file(self, request_file_id=None):
        """
        :param request_file_id: file id to download
        :return: tuple: (raw bytes of downloaded file, filename)
        """
        file_id = None
        filename = None
        for file in self.all_files:
            if file["id"] == request_file_id:
                file_id = file["id"]
                filename = file["name"]
        file_data = {"alt": "media"}
        return (requests.get(f"https://www.googleapis.com/drive/v3/files/{file_id}",
                             params=file_data,
                             headers=self._auth_headers).content, filename)

    def delete(self, file_id):
        """
        Permanently deletes  a filename by id. Skips the trash. Be careful!
        :param file_id: id of file that should be deleted
        """
        r = requests.request("DELETE", f"https://www.googleapis.com/drive/v3/files/{file_id}",
                             headers=self._auth_headers)
        print(r.text)

    def _empty_trash(self):
        """
        Empty trash without ability to restore. Be careful!
        """
        r = requests.request("DELETE", "https://www.googleapis.com/drive/v3/files/trash",
                             headers=self._auth_headers)

    def _send_initial_request(self, file_path, parent_id=None):
        """
        Send initial request to prepare API to receive further requests to upload
        :param file_path: absolute path to file for upload
        :param parent_id: (optional) id of parent folder passed in `file_path`
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
        return requests.post("https://www.googleapis.com/upload/drive/v3/files?uploadType=resumable",
                             headers=headers, data=metadata)

    def _single_upload(self, file_path, parent_id=None):
        """
        Perform upload by one single request. Faster than multipart upload,
        but not renewable after lost connection.
        :param file_path: absolute path to file for upload
        :param parent_id: (optional) id of parent folder passed in `file_path`
        """
        response = self._send_initial_request(file_path, parent_id)
        resumable_uri = response.headers["location"]
        with open(file_path, "rb") as f:
            file_data = f.read()
        r = requests.put(resumable_uri, data=file_data,
                         headers=response.headers)
        return r.json()

    def _multipart_upload(self, file_path, parent_id=None):
        """
        Perform upload by few little requests. Slower than single upload,
        but more safer with unstable connection.
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
