import os
from cloudbackup import gdrive
from cloudbackup import yadisk


class RemoteStorage:
    def __init__(self):
        self.gdrive = gdrive.GDrive()
        self.yadisk = yadisk.YaDisk()

    def upload(self, storage, file_abs_path=None, multipart=True):
        uploaded_files = []
        if multipart:
            gdrive_upload = self.gdrive.multipart_upload
        else:
            gdrive_upload = self.gdrive.single_upload
        tree = os.walk(file_abs_path)
        if storage == 'gdrive':
            if os.path.isfile(file_abs_path):
                res = gdrive_upload(file_abs_path)
                uploaded_files.append(res)
            elif os.path.isdir(file_abs_path):
                parents = {}
                while True:
                    try:
                        root, dirs, filenames = next(tree)
                        parent_id = parents[os.path.split(root)[0]] if parents else []
                        # os.path.split returns pair (head, tail) of path
                        folder_id = self.gdrive.create_folder(os.path.split(root)[-1],
                                                              parent_id=parent_id)
                        if not filenames:
                            continue
                        for file in filenames:
                            res = gdrive_upload(os.path.join(root, file), parent_id=folder_id)
                            uploaded_files.append(res)
                        parents[root] = folder_id
                    except StopIteration:
                        break
            else:
                print('This directory or file doesn\'t exists')
        return uploaded_files
