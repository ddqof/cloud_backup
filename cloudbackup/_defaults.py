import os

DEFAULT_GOOGLE_TOKEN_PATH = os.path.join(os.path.dirname(__file__), "service", "google", "token.pickle")
TEST_GOOGLE_TOKEN_PATH = os.path.join(os.path.dirname(__file__), "service", "google", "test_token.pickle")
GOOGLE_CREDENTIALS_PATH = os.path.join(os.path.dirname(__file__), "service", "google", "credentials.json")
YANDEX_CREDENTIALS_PATH = os.path.join(os.path.dirname(__file__), "service", "yandex", "credentials.json")
DEFAULT_YANDEX_TOKEN_PATH = os.path.join(os.path.dirname(__file__), "service", "yandex", "token.pickle")
TEST_YANDEX_TOKEN_PATH = os.path.join(os.path.dirname(__file__), "service", "yandex", "test_token.pickle")
SUCCESS_MESSAGE_PATH = os.path.join(os.path.dirname(__file__), "service", "success_message.html")
FAILURE_MESSAGE_PATH = os.path.join(os.path.dirname(__file__), "service", "failure_message.html")
REDIRECT_HOST = "http://127.0.0.1"
REDIRECT_PORT = 8000
GDRIVE_SCOPE = "https://www.googleapis.com/auth/drive"
INACCURACY_SECONDS = 5
GDRIVE_OAUTH_LINK = "https://accounts.google.com/o/oauth2/v2/auth?"
YADISK_OAUTH_LINK = "https://oauth.yandex.ru/authorize?"