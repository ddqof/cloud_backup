class RemoteFile:

    def __init__(self, name, type, id):
        self.name = name
        self.type = type
        self.id = id

    def __str__(self):
        if self.type == "dir":
            file_type = "D"
        elif self.type == "file":
            file_type = "F"
        else:
            file_type = "S"
        return f"[{file_type}] {self.name} ({self.id})"

    def __eq__(self, other):
        return self.__dict__ == other.__dict__


class YaDiskFile(RemoteFile):
    """
    Class represents file object on YandexDisk storage
    """

    def __init__(self, meta_inf):
        """
        Create file object from JSON response

        Params:
            meta_inf: JSON contains raw file meta-information from
             YandexDisk API response
        """
        super().__init__(meta_inf["name"], meta_inf["type"], meta_inf["path"])
        self.created = meta_inf["created"]
        self.modified = meta_inf["modified"]
        try:
            self.download_link = meta_inf["file"]
        except KeyError:
            pass
        try:
            self.size = meta_inf["size"]
        except KeyError:
            pass
        try:
            self.mime_type = meta_inf["mime_type"]
        except KeyError:
            pass


class GDriveFile(RemoteFile):
    """
    Class represents file object on Google Drive storage
    """

    def __init__(self, meta_inf):
        """
        Create file object from JSON response

        Args:
            meta_inf: JSON contains raw file meta-information from
             GoogleDrive API response
        """
        self.mime_type = meta_inf["mimeType"]
        if self.mime_type == "application/vnd.google-apps.folder":
            type = "dir"
        elif self.mime_type.startswith("application/vnd.google-apps"):
            type = "g.suite"
        else:
            type = "file"
        super().__init__(meta_inf["name"], type, meta_inf["id"])
