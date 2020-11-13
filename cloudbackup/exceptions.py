class YaDiskApiResponseException(Exception):
    def __init__(self, status_code, message):
        self.status_code = status_code
        self.message = message


class IncorrectPathException(Exception):
    """
    Raises when destination path contains ':' symbol that
    YandexDisk API cannot handle
    """
    def __init__(self, path):
        self.message = f"Path: {path} mustn't include a `:` character"
