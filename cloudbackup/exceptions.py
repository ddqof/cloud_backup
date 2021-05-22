class ApiResponseException(Exception):
    """
    Raises when API cannot handle given request
    """

    def __init__(self, status_code, message):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


class FileIsNotDownloadableException(Exception):

    def __init__(self, file):
        """
        :param file: file path or file id
        """
        self.message = f"File: `{file}` isn't downloadable."
        super().__init__(self.message)


class CredentialsNotFoundException(Exception):

    def __init__(self, storage: str):
        self.message = f"Credentials file not found for {storage}."
        super(CredentialsNotFoundException, self).__init__(self.message)
