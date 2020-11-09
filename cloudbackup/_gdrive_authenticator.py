import json
import os
import datetime
import pickle
import re
import requests
from urllib.parse import urlencode
from .defaults import (GOOGLE_CREDENTIALS_PATH, GOOGLE_TOKEN_PATH,
                       SUCCESS_MESSAGE_PATH, REDIRECT_HOST, REDIRECT_PORT, GDRIVE_SCOPE)
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
            code, client = GDriveAuth._get_access_code_and_client(credentials)
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

    @staticmethod
    def _get_access_code_and_client(credentials):
        """
        :param credentials: credentials to access Google Drive api
        :return: client socket and access code to Google Drive api
        """
        keys = {"client_id": credentials["installed"]["client_id"],
                "redirect_uri": f"{REDIRECT_HOST}:{str(REDIRECT_PORT)}",
                "response_type": "code",
                "scope": GDRIVE_SCOPE,
                "access_type": "offline",
                }
        login_url = "https://accounts.google.com/o/oauth2/v2/auth?" + urlencode(keys)
        client, response = LocalServer.handle(login_url)
        return re.search(r"code=(\S+)[\s&]", response).group(1), client
