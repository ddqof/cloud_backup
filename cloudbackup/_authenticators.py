import json
import datetime
import pickle
import re
import os
import requests
from urllib.parse import urlencode
from ._defaults import (GOOGLE_CREDENTIALS_PATH, GOOGLE_TOKEN_PATH,
                        SUCCESS_MESSAGE_PATH, REDIRECT_HOST, REDIRECT_PORT, GDRIVE_SCOPE, YANDEX_CREDENTIALS_PATH,
                        YANDEX_TOKEN_PATH, FAILURE_MESSAGE_PATH)
from ._local_server import LocalServer


class GDriveAuth:
    @staticmethod
    def authenticate():
        """
        :return: token to access to Google Drive API
        """
        with open(GOOGLE_CREDENTIALS_PATH) as credentials_file:
            credentials = json.load(credentials_file)
        if os.path.exists(GOOGLE_TOKEN_PATH):
            with open(GOOGLE_TOKEN_PATH, "rb") as token_file:
                token_data = pickle.load(token_file)
            if token_data["expire_time"] < datetime.datetime.now():
                exchange_keys = {
                    "client_id": credentials["installed"]["client_id"],
                    "client_secret": credentials["installed"]["client_secret"],
                    "grant_type": "refresh_token",
                    "refresh_token": token_data["refresh_token"]
                }
                r = requests.post("https://oauth2.googleapis.com/token", data=exchange_keys)
                token_data["access_token"] = r.json()["access_token"]
                with open(GOOGLE_TOKEN_PATH, "wb") as token_file:
                    pickle.dump(token_data, token_file)
            return token_data["access_token"]
        else:
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
                "access_token": json_reply["access_token"],
                "refresh_token": json_reply["refresh_token"],
                "expire_time": datetime.datetime.now() + datetime.timedelta(0, json_reply["expires_in"])
                # add seconds to current time
            }
            with open(GOOGLE_TOKEN_PATH, "wb") as f:
                pickle.dump(token_data, f)
            with open(SUCCESS_MESSAGE_PATH) as f:
                message = f"HTTP/1.1 200 OK\r\n\r\n{f.read()}"
            client.send(message.encode())
            return token_data["access_token"]


class YaDiskAuth:
    @staticmethod
    def authenticate():
        """
        Get the access token to YandexDisk API requests
        :return: status message: access token or denied access message
        """
        if os.path.exists(YANDEX_TOKEN_PATH):
            with open(YANDEX_TOKEN_PATH, "rb") as token_file:
                token_data = pickle.load(token_file)
                if token_data["expire_time"] > datetime.datetime.now():
                    return token_data["access_token"]
        with open(YANDEX_CREDENTIALS_PATH) as credentials_file:
            credentials = json.load(credentials_file)
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
                client.send(message.encode())
            token_data = {
                "access_token": r["access_token"],
                "expire_time": datetime.datetime.now() + datetime.timedelta(0, r["expires_in"])
                # add seconds to current time
            }
            with open(YANDEX_TOKEN_PATH, "wb") as token_file:
                pickle.dump(token_data, token_file)
            return token_data["access_token"]
        except AttributeError:
            error_msg = re.search(r"/?error=(\S+)[&]", response).group(1)
            if error_msg == "access_denied":
                with open(FAILURE_MESSAGE_PATH) as f:
                    message = f"HTTP/1.1 200 OK\r\n\r\n{f.read()}"
                    client.send(message.encode())
        raise PermissionError("You should give access to operate with this app.")
