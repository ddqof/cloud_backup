import json
import datetime
import pickle
import re
import os
import socket
import webbrowser
import requests
from urllib.parse import urlencode
from ._defaults import (
    GOOGLE_CREDENTIALS_PATH,
    DEFAULT_GOOGLE_TOKEN_PATH,
    SUCCESS_MESSAGE_PATH,
    REDIRECT_HOST,
    REDIRECT_PORT,
    GDRIVE_SCOPE,
    YANDEX_CREDENTIALS_PATH,
    DEFAULT_YANDEX_TOKEN_PATH,
    FAILURE_MESSAGE_PATH,
    INACCURACY_SECONDS,
    GDRIVE_OAUTH_LINK,
    YADISK_OAUTH_LINK
)


class Authenticator:
    def __init__(self):
        self._client_socket = None

    def _handle_user_prompt(self, url):
        """
        Open url in browser to let user give permissions for using this app.

        :param url: url that should be opened
        :return: tuple(client_socket, response)
        """
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
            server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            server.bind(("localhost", REDIRECT_PORT))
            server.listen()
            webbrowser.open(url)
            self._client_socket, addr = server.accept()
            response = self._client_socket.recv(1024).decode()
            if "access_denied" in response:
                with open(FAILURE_MESSAGE_PATH) as f:
                    message = f"HTTP/1.1 200 OK\r\n\r\n{f.read()}"
                    self._client_socket.send(message.encode())
            else:
                return re.search(r"code=(\S+)[\s&]", response).group(1)

    def _dump_token_data(self, api_response, filename):
        """
        Dump token data from API to file using pickle.
        """
        expire_seconds = datetime.timedelta(0, api_response["expires_in"] -
                                            INACCURACY_SECONDS)
        token_data = {
            "access_token": api_response["access_token"],
            "refresh_token": api_response["refresh_token"],
            "expire_time": datetime.datetime.now() + expire_seconds
            # add seconds to current time
        }
        with open(filename, "wb") as file:
            pickle.dump(token_data, file)

    def _send_successful_message(self):
        """
        Sending HTML message if user granted permissions.
        """
        with open(SUCCESS_MESSAGE_PATH) as f:
            message = f"HTTP/1.1 200 OK\r\n\r\n{f.read()}"
        self._client_socket.send(message.encode())

    def get_gdrive_token(self, token_file_path=DEFAULT_GOOGLE_TOKEN_PATH):
        """
        :return: token to access to Google Drive API
        """
        with open(GOOGLE_CREDENTIALS_PATH) as credentials_file:
            credentials = json.load(credentials_file)
        if os.path.exists(token_file_path):
            with open(token_file_path, "rb") as token_file:
                token_data = pickle.load(token_file)
            if token_data["expire_time"] < datetime.datetime.now():
                exchange_keys = {
                    "client_id": credentials["installed"]["client_id"],
                    "client_secret": credentials["installed"]["client_secret"],
                    "grant_type": "refresh_token",
                    "refresh_token": token_data["refresh_token"]
                }
                api_token_response = self._get_gdrive_tokens_from_api(
                    exchange_keys)
                token_data["access_token"] = api_token_response["access_token"]
                expire_seconds = datetime.timedelta(
                    0, api_token_response["expires_in"] - INACCURACY_SECONDS)
                token_data["expire_time"] = (
                        datetime.datetime.now() + expire_seconds)
                with open(token_file_path, "wb") as token_file:
                    pickle.dump(token_data, token_file)
            return token_data["access_token"]
        else:
            keys = {"client_id": credentials["installed"]["client_id"],
                    "redirect_uri": f"{REDIRECT_HOST}:{str(REDIRECT_PORT)}",
                    "response_type": "code",
                    "scope": GDRIVE_SCOPE,
                    "access_type": "offline",
                    }
            login_url = GDRIVE_OAUTH_LINK + urlencode(keys)
            response = self._handle_user_prompt(login_url)
            exchange_keys = {
                "client_id": credentials["installed"]["client_id"],
                "client_secret": credentials["installed"]["client_secret"],
                "code": response,
                "grant_type": "authorization_code",
                "redirect_uri": f"{REDIRECT_HOST}:{str(REDIRECT_PORT)}",
            }
            api_token_response = self._get_gdrive_tokens_from_api(
                exchange_keys)
            self._dump_token_data(api_token_response, token_file_path)
            self._send_successful_message()
            return api_token_response["access_token"]

    def _get_gdrive_tokens_from_api(self, data):
        """
        Send a request to Google Drive API for getting access and
        refresh token or can be used for updating access token by
        sending refresh token

        Params:
            data: dict with application data that Google give when
            you create app.
        Returns:
            Json response from Google Drive API
        """
        return requests.post(
            "https://oauth2.googleapis.com/token",
            data=data
        ).json()

    def get_yadisk_token(self, token_file_path=DEFAULT_YANDEX_TOKEN_PATH):
        """
        Get the access token to YandexDisk API requests
        :return: status message: access token or denied access message
        """
        if os.path.exists(token_file_path):
            with open(token_file_path, "rb") as token_file:
                token_data = pickle.load(token_file)
                if token_data["expire_time"] > datetime.datetime.now():
                    return token_data["access_token"]
        else:
            with open(YANDEX_CREDENTIALS_PATH) as credentials_file:
                credentials = json.load(credentials_file)
            keys = {
                "response_type": "code",
                "client_id": credentials["client_id"]
            }
            code = self._handle_user_prompt(
                YADISK_OAUTH_LINK + urlencode(keys))
            exchange_keys = {
                "grant_type": "authorization_code",
                "code": code,
                "client_id": credentials["client_id"],
                "client_secret": credentials["client_secret"]
            }
            api_token_response = self._get_yadisk_tokens_from_api(
                exchange_keys)
            self._dump_token_data(api_token_response, token_file_path)
            self._send_successful_message()
            return api_token_response["access_token"]

    def _get_yadisk_tokens_from_api(self, data):
        """
        Send a request to Yandex Disk API for getting access and
        refresh token or can be used for updating access token by
        sending refresh token

        Params:
            data: dict with application data that Yandex give
            when you create app.
        Returns:
            Json response from Yandex Disk API
        """
        return requests.post(
            "https://oauth.yandex.ru/token",
            data=data
        ).json()
