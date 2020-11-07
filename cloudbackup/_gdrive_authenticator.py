import json
import os
import datetime
import re
import socket
import webbrowser
import requests
import configparser
from urllib.parse import urlencode
from .defaults import (GOOGLE_CREDENTIALS_PATH, GOOGLE_TOKEN_PATH,
                       SUCCESS_MESSAGE_PATH, REDIRECT_HOST, REDIRECT_PORT)


class GDriveAuth:
    def __init__(self):
        self.scope = "https://www.googleapis.com/auth/drive"

    def authenticate(self):
        """
        :return: token to access to Google Drive API
        """
        config = configparser.ConfigParser()
        if self._token_is_valid(config):
            return config["token"]["id"]
        with open(GOOGLE_CREDENTIALS_PATH) as f:
            credentials = json.load(f)
            code, client_socket = self._get_access_code_and_client(credentials)
        exchange_keys = {
            "client_id": credentials["installed"]["client_id"],
            "client_secret": credentials["installed"]["client_secret"],
            "code": code,
            "grant_type": "authorization_code",
            "redirect_uri": "http://127.0.0.1:8000",
        }
        r = requests.post("https://oauth2.googleapis.com/token",
                          data=exchange_keys)
        expire_time = datetime.datetime.now() + datetime.timedelta(0, r.json()[
            "expires_in"])  # add seconds to current time

        access_token = r.json()["access_token"]
        config["token"] = {}
        config["token"]["id"] = access_token
        config["token"]["expire_time"] = repr(expire_time)

        with open(GOOGLE_TOKEN_PATH, "w") as configfile:
            config.write(configfile)
        with open(SUCCESS_MESSAGE_PATH) as f:
            message = f"HTTP/1.1 200 OK\r\n\r\n{f.read()}"
        client_socket.send(message.encode())
        return access_token

    def _token_is_valid(self, config):
        """
        :param config: config where token is stored
        :return: whether token expired
        """
        if os.path.exists(GOOGLE_TOKEN_PATH):
            config.read(GOOGLE_TOKEN_PATH)
            if config["token"]["expire_time"] != "0":
                expire_time = eval(config["token"]["expire_time"])
                if datetime.datetime.now() < expire_time:
                    return True
        return False

    def _get_access_code_and_client(self, credentials):
        """
        :param credentials: credentials to access Google Drive api
        :return: client socket and access code to Google Drive api
        """
        keys = {"client_id": credentials["installed"]["client_id"],
                "redirect_uri": REDIRECT_HOST + ":" + str(REDIRECT_PORT),
                "response_type": "code",
                "scope": self.scope,
                "access_type": "offline",
                }
        login_url = "https://accounts.google.com/o/oauth2/v2/auth?" + urlencode(keys)
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind(("localhost", REDIRECT_PORT))
        s.listen()
        webbrowser.open(login_url)
        client, addr = s.accept()
        response = client.recv(1024).decode()
        return re.search("code=(.*)?&", response).group(1), client
