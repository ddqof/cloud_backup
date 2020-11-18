import json
import datetime
import pickle
import re
import requests
from urllib.parse import urlencode
from .defaults import (GOOGLE_CREDENTIALS_PATH, GOOGLE_TOKEN_PATH,
                       SUCCESS_MESSAGE_PATH, REDIRECT_HOST, REDIRECT_PORT, GDRIVE_SCOPE, YANDEX_CREDENTIALS_PATH,
                       YANDEX_TOKEN_PATH, FAILURE_MESSAGE_PATH)
from ._local_server import LocalServer
from ._file_operations import FileOperations


class GDriveAuth:
    @staticmethod
    def authenticate():
        """
        :return: token to access to Google Drive API
        """
        token = FileOperations.check_token(GOOGLE_TOKEN_PATH)
        if token is not None:
            return token
        with open(GOOGLE_CREDENTIALS_PATH) as f:
            credentials = json.load(f)
            keys = {"client_id": credentials["installed"]["client_id"],
                    "redirect_uri": f"{REDIRECT_HOST}:{str(REDIRECT_PORT)}",
                    "response_type": "code",
                    "scope": GDRIVE_SCOPE,
                    "access_type": "offline",
                    }
            login_url = "https://accounts.google.com/o/oauth2/v2/auth?" + urlencode(keys)
            client, response = LocalServer.handle(login_url)
            code = re.search(r"code=(\S+)[\s&]", response).group(1)
        exchange_keys = {
            "client_id": credentials["installed"]["client_id"],
            "client_secret": credentials["installed"]["client_secret"],
            "code": code,
            "grant_type": "authorization_code",
            "redirect_uri": f"{REDIRECT_HOST}:{str(REDIRECT_PORT)}",
        }
        json_reply = requests.post("https://oauth2.googleapis.com/token",
                                   data=exchange_keys).json()
        token_data = {
            "token": json_reply["access_token"],
            "expire_time": datetime.datetime.now() + datetime.timedelta(0, json_reply["expires_in"])
            # add seconds to current time
        }
        with open(GOOGLE_TOKEN_PATH, "wb") as f:
            pickle.dump(token_data, f)
        with open(SUCCESS_MESSAGE_PATH) as f:
            message = f"HTTP/1.1 200 OK\r\n\r\n{f.read()}"
        client.send(message.encode())
        return token_data["token"]


class YaDiskAuth:
    @staticmethod
    def authenticate():
        """
        Get the access token to YandexDisk API requests
        :return: status message: access token or denied access message
        """
        token = FileOperations.check_token(YANDEX_TOKEN_PATH)
        if token is not None:
            return token
        with open(YANDEX_CREDENTIALS_PATH) as f:
            credentials = json.load(f)
        keys = {
            "response_type": "code",
            "client_id": credentials["client_id"]
        }
        client, response = LocalServer.handle("https://oauth.yandex.ru/authorize?" + urlencode(keys))
        try:
            code = re.search(r"code=(\S+)[\s&]", response).group(1)
            exchange_keys = {
                "grant_type": "authorization_code",
                "code": code,
                "client_id": credentials["client_id"],
                "client_secret": credentials["client_secret"]
            }
            r = requests.post("https://oauth.yandex.ru/token", data=exchange_keys).json()
            with open(SUCCESS_MESSAGE_PATH) as f:
                message = f"HTTP/1.1 200 OK\r\n\r\n{f.read()}"
            token_data = {
                "token": r["access_token"],
                "expire_time": datetime.datetime.now() + datetime.timedelta(0, r["expires_in"])
                # add seconds to current time
            }
            with open(YANDEX_TOKEN_PATH, "wb") as f:
                pickle.dump(token_data, f)
            status = token_data["token"]
        except AttributeError:
            error_msg = re.search(r"/?error=(\S+)[&]", response).group(1)
            if error_msg == "access_denied":
                with open(FAILURE_MESSAGE_PATH) as f:
                    message = f"HTTP/1.1 200 OK\r\n\r\n{f.read()}"
            status = error_msg
        client.send(message.encode())
        return status
