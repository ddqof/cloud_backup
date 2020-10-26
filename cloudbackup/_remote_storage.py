import os
from cloudbackup import gdrive
from cloudbackup import yadisk


class RemoteStorage:
    def __init__(self):
        self.gdrive = gdrive.GDrive()
        self.yadisk = yadisk.YaDisk()

    def upload(self, storage, path=None):
        tree = os.walk(path)
        if storage == 'gdrive':
            while True:
                try:
                    current_directory_objects = next(tree)  # tuple (dirpath, dirnames, filenames)
                    root = current_directory_objects[0]
                    for file in current_directory_objects[2]:
                        self.gdrive.multipart_request_upload_file(filename=file, file_root=root)
                    folder_name = root.split(os.path.sep)[-1]
                    self.gdrive.create_folder(folder_name)
                except StopIteration:
                    return


