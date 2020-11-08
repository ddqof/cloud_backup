import json
import os
import pickle
import datetime
import re
import requests
from urllib.parse import urlencode
from .defaults import (YANDEX_CREDENTIALS_PATH, SUCCESS_MESSAGE_PATH,
                       FAILURE_MESSAGE_PATH, YANDEX_TOKEN_PATH)
from ._local_server import LocalServer


class YaDiskAuth:
    def authenticate(self):
        """
        Get the access token to YandexDisk API requests
        :return: status message: access token or denied access message
        """
        token = self._check_token()
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

    def _check_token(self):
        """
        :return: token if it's not expired, else None
        """
        if os.path.exists(YANDEX_TOKEN_PATH):
            with open(YANDEX_TOKEN_PATH) as f:
                token_data = pickle.load(f)
                expire_time = eval(token_data["expire_time"])
                if datetime.datetime.now() < expire_time:
                    return token_data["token"]
        return None
