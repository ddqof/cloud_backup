from collections import namedtuple
import json
import os
import mimetypes
import requests
from ._authenticators import GDriveAuth
from ._file_objects import GDriveFile
from .exceptions import ApiResponseException, FileIsNotDownloadableException


class GDrive:
    """
    Implements access to GoogleDrive API.
    """

    def __init__(self):
        self._auth_headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {GDriveAuth.authenticate()}"
        }

    def download(self, file_id) -> bytes:
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

    def lsdir(self, dir_id=None, trashed=False, owners=None, page_size=20, page_token=None,
              order_by="modifiedTime") -> namedtuple("Page", "files next_page_token"):
        """
        Make request to get list of `page_size` size consists of files and directories in
        directory with specified dir_id.

        Args:
            dir_id: If None then list all files, else list files in a directory with given id
            trashed: Whether to list files from the trash
            owners: List or files owners
            page_size: Files count on one page (set value from 1 to 1000)
            page_token: Token of the next page
            order_by: Sort key. Valid keys are: 'createdTime', 'folder' (folders will show first in the list),
              'modifiedTime', 'name', 'recency', 'viewedByMeTime'. Each key sorts ascending by default,
               but may be reversed with the 'desc' modifier. For example: modifiedTime desc.

        Returns:
            |namedtuple| containing list of `page_size` size consists of GDriveFile objects and next page token.
                If next page token is None, then there are no more pages.

        Raises:
            ApiResponseException: an error occurred accessing API
        """
        if dir_id:
            if owners:
                query = f"trashed={trashed} and '{dir_id}' in parents and '{','.join(owners)}' in owners"
            else:
                query = f"trashed={trashed} and '{dir_id}' in parents"
        else:
            if owners:
                query = f"trashed={trashed} and '{','.join(owners)}' in owners"
            else:
                query = f"trashed={trashed}"
        flags = {
            "q": query,
            "pageSize": page_size,
            "orderBy": order_by,
            "fields": "files(name, mimeType, id), nextPageToken",
            "pageToken": page_token,
        }
        r = requests.get("https://www.googleapis.com/drive/v3/files",
                         params=flags, headers=self._auth_headers)
        GDrive._check_status(r)
        Page = namedtuple("Page", "files next_page_token")
        r = r.json()
        if "nextPageToken" in r:
            return Page([GDriveFile(file) for file in r["files"]], r["nextPageToken"])
        else:
            return Page([GDriveFile(file) for file in r["files"]], None)

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
            r = requests.request("DELETE", f"https://www.googleapis.com/drive/v3/files/{file_id}",
                                 headers=self._auth_headers)
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

    def get_upload_link(self, file_path, parent_id=None) -> str:
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
        }
        headers.update(self._auth_headers)
        metadata = {"name": filename}
        if parent_id is not None:
            metadata["parents"] = [parent_id]
        metadata = json.dumps(metadata)
        r = requests.post("https://www.googleapis.com/upload/drive/v3/files?uploadType=resumable",
                          headers=headers, data=metadata)
        GDrive._check_status(r)
        return r.headers["location"]

    def upload_entire_file(self, link, file_data):
        r = requests.put(link, data=file_data)
        GDrive._check_status(r)

    def upload_chunk(self, link, file_data, uploaded_size, chunk_size, file_size):
        """

        Returns:
            |namedtuple| UploadStatus("code", "received"). If code equals 200 upload is completed, if 308 then
            server received chunk and you can proceed uploading another chunks.
        """
        chunk_info = {
            "Content-Length": chunk_size,
            "Content-Range": f"bytes {str(uploaded_size)}-{str(uploaded_size + chunk_size - 1)}/{file_size}"
        }
        r = requests.put(link, data=file_data, headers=chunk_info)
        GDrive._check_status(r)
        UploadStatus = namedtuple("UploadStatus", ["code", "received"])
        return UploadStatus(r.status_code, int(r.headers["range"].split("-")[1]) + 1)
        # range header looks like "bytes=0-n", where n - received bytes

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
