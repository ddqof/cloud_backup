import os
from cloudbackup import gdrive
from cloudbackup import yadisk


class RemoteStorage:
    def __init__(self, storage):
        self.name = storage
        if self.name == "gdrive":
            self.gdrive = gdrive.GDrive()
        if self.name == "yadisk":
            self.yadisk = yadisk.YaDisk()

    def upload(self, file_abs_path=None, multipart=True):
        # uploaded_files = []
        if multipart:
            gdrive_upload = self.gdrive.multipart_upload
        else:
            gdrive_upload = self.gdrive.single_upload
        tree = os.walk(file_abs_path)
        if self.name == "gdrive":
            if os.path.isfile(file_abs_path):
                res = gdrive_upload(file_abs_path)
                # uploaded_files.append(res)
            elif os.path.isdir(file_abs_path):
                parents = {}
                for root, dirs, filenames in tree:
                    parent_id = parents[os.path.split(root)[0]] if parents else []
                    # os.path.split returns pair (head, tail) of path
                    folder_id = self.gdrive.create_folder(os.path.split(root)[-1],
                                                          parent_id=parent_id)
                    if not filenames:
                        continue
                    for file in filenames:
                        res = gdrive_upload(os.path.join(root, file), parent_id=folder_id)
                        # uploaded_files.append(res)
                    parents[root] = folder_id
            else:
                return "This directory or file doesn\'t exists"
        # return uploaded_files

    def list_files(self):
        """
        Return dict of file which contains pairs like file_name: mimeType
        """
        files = {}
        raw_files = self.gdrive.get_files()
        for line in raw_files:
            files[line["name"]] = line["mimeType"]
        return files

    def download(self, filename, path=None):
        try:
            file_bytes = self.gdrive.download(filename=filename)
        except FileNotFoundError:
            return f"File: `{filename}` not found"
        if path is None:
            dl_path = filename
        else:
            dl_path = os.path.join(path, filename)
        with open(dl_path, "wb+") as f:
            f.write(file_bytes)
        return f"Successfully download file: {filename} to {path} directory"

    def delete(self, filename):
        self.gdrive._delete(filename)
