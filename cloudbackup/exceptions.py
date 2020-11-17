class ApiResponseException(Exception):
    """
    Raises when API cannot handle given request
    """
    def __init__(self, status_code, message):
        self.status_code = status_code
        self.message = message


class IncorrectPathException(Exception):
    """
    Raises when destination path contains ':' symbol that
    YandexDisk API cannot handle
    """

    def __init__(self, path):
        self.message = f"Path: {path} must not include a `:` character"


class AutocompleteFileIdException(Exception):
    """
    Raises when there is no File Id starts with given Request Id on GoogleDrive storage
    """

    def __init__(self, file_id):
        self.message = f"There is no file with {file_id}"
