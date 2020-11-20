import os

GOOGLE_TOKEN_PATH = os.path.join(os.path.dirname(__file__), "service", "google", "token.pickle")
GOOGLE_CREDENTIALS_PATH = os.path.join(os.path.dirname(__file__), "service", "google", "credentials.json")
YANDEX_CREDENTIALS_PATH = os.path.join(os.path.dirname(__file__), "service", "yandex", "credentials.json")
YANDEX_TOKEN_PATH = os.path.join(os.path.dirname(__file__), "service", "yandex", "token.pickle")
SUCCESS_MESSAGE_PATH = os.path.join(os.path.dirname(__file__), "service", "success_message.html")
FAILURE_MESSAGE_PATH = os.path.join(os.path.dirname(__file__), "service", "failure_message.html")
REDIRECT_HOST = "http://127.0.0.1"
REDIRECT_PORT = 8000
GDRIVE_SCOPE = "https://www.googleapis.com/auth/drive"
GDRIVE_SORT_KEYS = {
        "name": "name",
        "modified": "modifiedTime",
        "created": "createdTime",
        "size": "quotaBytesUsed",
        "folder": "folder",
        "rev_name": "name desc",
        "rev_modified": "modifiedTime desc",
        "rev_created": "createdTime desc",
        "rev_size": "quotaBytesUsed desc",
        "rev_folder": "folder desc",
    }
YADISK_SORT_KEYS = {
    "name": "name",
    "created": "created",
    "modified": "modified",
    "size": "size",
    "path": "rev path",
    "rev_name": "-name",
    "rev_created": "-created",
    "rev_modified": "-modified",
    "rev_size": "-size",
    "rev_path": "-path",
}