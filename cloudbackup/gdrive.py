import json
import os
import mimetypes
import datetime
import re
import socket
import webbrowser
import requests
import configparser
from urllib.parse import urlencode
from .defaults import (GOOGLE_CREDENTIALS_PATH, GOOGLE_TOKEN_PATH,
                       SUCCESS_MESSAGE_PATH, REDIRECT_HOST, REDIRECT_PORT)


class GDrive:
    def __init__(self):
        self.scope = "https://www.googleapis.com/auth/drive"
        self.token = self._authenticate()
        self._auth_headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.token}"
        }
        self.directories_history = ["root"]
        self.current_directory = "root"
        self.files = self._get_files()

    def _authenticate(self):
        """
        :return: token to access to Google Drive API
        """
        config = configparser.ConfigParser()
        if self._token_is_valid(config):
            return config["token"]["id"]
        with open(GOOGLE_CREDENTIALS_PATH) as f:
            credentials = json.load(f)
            code, client_socket = self._get_access_code_and_client(credentials)
        exchange_keys = {
            "client_id": credentials["installed"]["client_id"],
            "client_secret": credentials["installed"]["client_secret"],
            "code": code,
            "grant_type": "authorization_code",
            "redirect_uri": "http://127.0.0.1:8000"
        }
        r = requests.post("https://oauth2.googleapis.com/token",
                          data=exchange_keys)
        expire_time = datetime.datetime.now() + datetime.timedelta(0, r.json()[
            "expires_in"])  # add seconds to current time

        access_token = r.json()["access_token"]
        config["token"] = {}
        config["token"]["id"] = access_token
        config["token"]["expire_time"] = repr(expire_time)

        with open(GOOGLE_TOKEN_PATH, "w") as configfile:
            config.write(configfile)
        with open(SUCCESS_MESSAGE_PATH) as f:
            message = f"HTTP/1.1 200 OK\r\n\r\n{f.read()}"
        client_socket.send(message.encode())
        return access_token

    def _token_is_valid(self, config):
        """
        :param config: config where token is stored
        :return: whether token expired
        """
        if os.path.exists(GOOGLE_TOKEN_PATH):
            config.read(GOOGLE_TOKEN_PATH)
            if config["token"]["expire_time"] != "0":
                expire_time = eval(config["token"]["expire_time"])
                if datetime.datetime.now() < expire_time:
                    return True
        return False

    def _get_access_code_and_client(self, credentials):
        """
        :param credentials: credentials to access Google Drive api
        :return: client socket and access code to Google Drive api
        """
        keys = {"client_id": credentials["installed"]["client_id"],
                "redirect_uri": REDIRECT_HOST + ":" + str(REDIRECT_PORT),
                "response_type": "code",
                "scope": self.scope}
        login_url = "https://accounts.google.com/o/oauth2/v2/auth?" + urlencode(keys)
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind(("localhost", REDIRECT_PORT))
        s.listen()
        webbrowser.open(login_url)
        client, addr = s.accept()
        response = client.recv(1024).decode()
        return re.search("code=(.*)?&", response).group(1), client

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
                parent_id = parents[os.path.split(root)[0]] if parents else []
                # os.path.split returns pair (head, tail) of path
                folder_id = self._create_folder(os.path.split(root)[-1],
                                                parent_id=parent_id)
                if not filenames:
                    continue
                for file in filenames:
                    upload(os.path.join(root, file), parent_id=folder_id)
                parents[root] = folder_id
                return "Download completed"
        else:
            return "This directory or file doesn\'t exists"

    def download(self, filename, path=None):
        """
        Download file to Google Drive storage
        :param filename: name of file to download
        :param path: (optional) pass absolute path where you want to store downloaded file
        :return: status message
        """
        try:
            file_bytes = self._download_file(filename=filename)
        except FileNotFoundError:
            return f"File: `{filename}` not found"
        if path is None:
            dl_path = filename
            path = "present working"
        else:
            dl_path = os.path.join(path, filename)
        with open(dl_path, "wb+") as f:
            f.write(file_bytes)
        return f"Successfully download file: {filename} to {path} directory"

    def list_files(self):
        """
        Return dict of files which contain pairs like file_name: mimeType
        """
        files = {}
        for line in self.files:
            files[line["name"]] = line["mimeType"]
        return files

    def change_directory(self, directory):
        if len(self.directories_history) > 1 and directory == self.directories_history[-2]:
            self.directories_history.pop()
            self.current_directory = directory
            self.files = self._get_files()
            return f"Switched to {directory}"
        else:
            for file in self.files:
                if file["name"] == directory:
                    self.directories_history.append(directory)
                    self.current_directory = directory
                    self.files = self._get_files()
                    return f"Switched to {directory}"
        return f"{directory}: No such directory"

    def _create_folder(self, name, parent_id=None):
        metadata = {
            "name": name,
            "mimeType": "application/vnd.google-apps.folder",
            "parents": [parent_id] if parent_id else []
        }
        r = requests.post("https://www.googleapis.com/drive/v3/files",
                          headers=self._auth_headers, data=json.dumps(metadata))
        return r.json()["id"]

    def _get_files(self, trashed=False, list_all=False):
        """
        Return list of files on Google Drive storage
        :param trashed: whether to show files that are in the trash
        :return: JSON file that includes files info
        """
        if self.current_directory == "root":
            flags = {
                "q": f"trashed={trashed}" if list_all
                else f"trashed={trashed} and 'root' in parents"
            }
        else:
            flags = {
                "q": f"trashed={trashed}" if list_all
                else f"trashed={trashed} and '{self._get_id_by_filename(self.directories_history[-1])}' in parents"
            }

        json_r = requests.get("https://www.googleapis.com/drive/v3/files",
                              params=flags, headers=self._auth_headers).json()
        return json_r["files"]

    def _get_id_by_filename(self, filename):
        """
        Return id by filename.
        """
        for file in self._get_files(list_all=True):
            if file["name"] == filename:
                return file["id"]

    def _download_file(self, filename=None):
        """
        :param filename: filename to download
        :return: raw bytes of downloaded file
        """
        file_id = self._get_id_by_filename(filename)
        file_data = {"alt": "media"}
        return requests.get(f"https://www.googleapis.com/drive/v3/files/{file_id}",
                            params=file_data,
                            headers=self._auth_headers).content

    def delete(self, filename):
        """
        Permanently deletes  a filename. Skips the trash. Be careful!
        :param filename: filename that should be deleted
        """
        file_id = self._get_id_by_filename(filename)
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
        r = requests.put(resumable_uri, data=open(file_path, "rb").read(),
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
                    print("Chunk uploaded successfully")
                    break
                diff = int(r.headers["range"].split("-")[1]) + 1 - uploaded_size
                # range header looks like "bytes=0-n", where n - received bytes
                file.seek(diff, 1)  # second parameter means seek relative to the current position
