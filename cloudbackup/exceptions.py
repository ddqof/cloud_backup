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


class RemoteFileNotFoundException(Exception):
    """
    Raises when there is no File Id starts with given Request Id on GoogleDrive storage
    """

    def __init__(self, file_id):
        self.message = f"There is no file with id: {file_id}."
        super().__init__(self.message)  # TODO: лучше организовать исключения, например нужно для gdrive принимать id, а для yadisk path


class FileIsNotDownloadableException(Exception):

    def __init__(self, file):
        self.message = f"G.Suite file {file.name} ({file.id})  isn't downloadable."
        super().__init__(self.message)
