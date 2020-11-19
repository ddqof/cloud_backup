class YaDiskFile:
    """
    Class represents file object on YandexDisk storage
    """

    def __init__(self, meta_inf):
        """
        Create file object from JSON response

        Params:
            meta_inf: JSON contains raw file meta-information from YandexDisk API response
        """
        self.name = meta_inf["name"]
        self.created = meta_inf["created"]
        self.modified = meta_inf["modified"]
        self.resource_id = meta_inf["resource_id"]
        self.path = meta_inf["path"]
        self.type = meta_inf["type"]
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

    def __str__(self):
        return f"YaDiskFileObject: {self.name}"


class GDriveFile:
    """
    Class represents file object on Google Drive storage
    """

    def __init__(self, meta_inf):
        """
        Create file object from JSON response

        Args:
            meta_inf: JSON contains raw file meta-information from GoogleDrive API response
        """
        self.id = meta_inf["id"]
        self.name = meta_inf["name"]
        self.mime_type = meta_inf["mimeType"]
        try:
            self.parents = meta_inf["parents"]
        except KeyError:
            pass

    def __str__(self):
        return f"GDriveFileObject: {self.name}"
