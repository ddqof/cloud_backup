class ApiResponseException(Exception):
    """
    Raises when API cannot handle given request
    """

    def __init__(self, status_code, message):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


class IncorrectPathException(Exception):
    """
    Raises when destination path contains ':' symbol that
    YandexDisk API cannot handle
    """

    def __init__(self, path):
        self.message = f"Path: {path} must not include a `:` character."
        super().__init__(self.message)


class FileIsNotDownloadableException(Exception):

    def __init__(self, file):
        """
        :param file: file path or file id
        """
        self.message = f"File: `{file}` isn't downloadable."
        super().__init__(self.message)
