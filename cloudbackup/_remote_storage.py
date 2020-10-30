import os
from cloudbackup import gdrive
from cloudbackup import yadisk


class RemoteStorage:
    def __init__(self):
        self.gdrive = gdrive.GDrive()
        self.yadisk = yadisk.YaDisk()

    def upload(self, storage, file_abs_path=None, multipart=False):
        if multipart:
            gdrive_upload = self.gdrive.multipart_upload
        else:
            gdrive_upload = self.gdrive.single_upload
        tree = os.walk(file_abs_path)
        if storage == 'gdrive':
            if os.path.isfile(file_abs_path):
                gdrive_upload(file_abs_path)
            elif os.path.isdir(file_abs_path):
                while True:
                    try:
                        current_directory_objects = next(tree)  # tuple (dirpath, dirnames, filenames)
                        if len(current_directory_objects[2]) == 0:
                            return
                        root = current_directory_objects[0]
                        for file in current_directory_objects[2]:
                            gdrive_upload(os.path.join(root, file))
                        folder_name = root.split(os.path.sep)[-1]
                        self.gdrive.create_folder(folder_name)
                    except StopIteration:
                        break
            else:
                print('This directory or file doesn\'t exists')
