import json
import os
import datetime
import re
import socket
import webbrowser
import requests
import configparser
from getpass import getpass
from .defaults import (GOOGLE_CREDENTIALS_PATH, GOOGLE_TOKEN_PATH, SUCCESS_MESSAGE_PATH, FAILURE_MESSAGE_PATH,
                       REDIRECT_HOST, REDIRECT_PORT)


class RemoteStorage:
    def __init__(self):
        self.gdrive_token = self.google_sign_in()
        self.yandex_token = self.yandex_sign_in()

    def google_sign_in(self):
        config = configparser.ConfigParser()
        config.read(GOOGLE_TOKEN_PATH)
        if config['token']['expire_time'] != '0':
            expire_time = eval(config['token']['expire_time'])
            if datetime.datetime.now() < expire_time:
                return config['token']['id']
        else:
            with open(GOOGLE_CREDENTIALS_PATH) as f:
                creds = json.load(f)
            keys = {'client_id': creds['installed']['client_id'],
                    'redirect_uri': REDIRECT_HOST + ':' + REDIRECT_PORT,
                    'response_type': 'code',
                    'scope': 'https://www.googleapis.com/auth/drive'}
            login_url = 'https://accounts.google.com/o/oauth2/v2/auth?scope={}' \
                        '&redirect_uri={}&response_type={}&client_id={}'
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            s.bind((REDIRECT_HOST, REDIRECT_PORT))
            s.listen()
            webbrowser.open(
                login_url.format(keys['scope'], keys['redirect_uri'], keys['response_type'], keys['client_id']))
            client, addr = s.accept()
            response = client.recv(1024).decode()
            code = re.search('code=(.*)?&', response).group(1)
            exchange_keys = {
                'client_id': creds['installed']['client_id'],
                'client_secret': creds['installed']['client_secret'],
                'code': code,
                'grant_type': 'authorization_code',
                'redirect_uri': 'http://127.0.0.1:8000'

            }
            r = requests.post('https://oauth2.googleapis.com/token',
                              data=exchange_keys)
            expire_time = datetime.datetime.now() + datetime.timedelta(0, r.json()[
                'expires_in'])  # add seconds to current time
            try:
                access_token = r.json()['access_token']
                config['token']['id'] = access_token
                config['token']['expire_time'] = repr(expire_time)
                with open(GOOGLE_TOKEN_PATH, 'w') as configfile:
                    config.write(configfile)
                with open(SUCCESS_MESSAGE_PATH) as f:
                    message = f'HTTP/1.1 200 OK\r\n\r\n{f.read()}'
                client.send(message.encode())
                return access_token
            except KeyError:
                with open(FAILURE_MESSAGE_PATH) as f:
                    message = f'HTTP/1.1 200 OK\r\n\r\n{f.read()}'
                client.send(message.encode())
                return None

    def yandex_sign_in(self):
        try:
            with open('cloudbackup/service/yandex/yandex_token.txt') as f:
                access_token = f.read()
        except FileNotFoundError:
            webbrowser.open(
                'https://oauth.yandex.ru/authorize?'
                'response_type=code&client_id=2d29d874333d4f70ac74bf3890456ade')
            code = getpass('Please input your code: ')
            access_token = None
            while access_token is None:
                keys = {'grant_type': 'authorization_code',
                        'code': code,
                        'client_id': '2d29d874333d4f70ac74bf3890456ade',
                        'client_secret': 'ace19a7dc359420ca09bd3c6fd6a8184'}
                r = requests.post('https://oauth.yandex.ru/token', data=keys)
                try:
                    return r.json()['access_token']
                except KeyError:
                    code = getpass('Wrong code. Please input it again: ')
                    pass

    def upload(self, storage, filename, zip=False):
        r = requests.post('https://www.googleapis.com/upload/drive/v3/files?uploadType=resumable',
                          auth=('Bearer', self.gdrive_token))
        # print(f'request on upload is {r.json()}')
        # if r.status_code == 200:
        #     location = r.headers['location']
        #     file_data = {'name': date + ' ' + filename}
        #     upload_request = requests.put(location, data=file_data, headers=headers)
        # else:
        #     print('Got non 200 http repsonse status code')
        # print('Successfully backed up to Google Drive')
