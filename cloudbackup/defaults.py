import os

GOOGLE_TOKEN_PATH = os.path.join(os.path.dirname(__file__), "service", "google", "token.pickle")
GOOGLE_CREDENTIALS_PATH = os.path.join(os.path.dirname(__file__), "service", "google", "credentials.json")
YANDEX_CREDENTIALS_PATH = os.path.join(os.path.dirname(__file__), "service", "yandex", "credentials.json")
YANDEX_TOKEN_PATH = os.path.join(os.path.dirname(__file__), "service", "yandex", "token.pickle")
SUCCESS_MESSAGE_PATH = os.path.join(os.path.dirname(__file__), "service", "success_message.html")
FAILURE_MESSAGE_PATH = os.path.join(os.path.dirname(__file__), "service", "failure_message.html")
REDIRECT_HOST = "http://127.0.0.1"
REDIRECT_PORT = 8000
