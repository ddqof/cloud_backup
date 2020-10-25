import json
import os
import mimetypes
import datetime
import re
import socket
import webbrowser
import requests
import configparser
from collections import namedtuple
from getpass import getpass
from .defaults import (GOOGLE_CREDENTIALS_PATH, GOOGLE_TOKEN_PATH, SUCCESS_MESSAGE_PATH,
                       FAILURE_MESSAGE_PATH, REDIRECT_HOST, REDIRECT_PORT)


class RemoteStorage:
    def __init__(self):
        self.gdrive_token = self.google_sign_in()
        self.yandex_token = self.yandex_sign_in()

    def check_token(self, config):
        if os.path.exists(GOOGLE_TOKEN_PATH):
            config.read(GOOGLE_TOKEN_PATH)
            if config['token']['expire_time'] != '0':
                expire_time = eval(config['token']['expire_time'])
                if datetime.datetime.now() < expire_time:
                    return config['token']['id']

    def get_access_code_and_client(self, credentials):
        keys = {'client_id': credentials['installed']['client_id'],
                'redirect_uri': REDIRECT_HOST + ':' + str(REDIRECT_PORT),
                'response_type': 'code',
                'scope': 'https://www.googleapis.com/auth/drive'}
        login_url = 'https://accounts.google.com/o/oauth2/v2/auth?scope={}' \
                    '&redirect_uri={}&response_type={}&client_id={}'
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind(('localhost', REDIRECT_PORT))
        s.listen()
        webbrowser.open(
            login_url.format(keys['scope'], keys['redirect_uri'], keys['response_type'], keys['client_id']))
        client, addr = s.accept()
        response = client.recv(1024).decode()
        return re.search('code=(.*)?&', response).group(1), client


    def google_sign_in(self):
        config = configparser.ConfigParser()
        self.check_token(config)
        with open(GOOGLE_CREDENTIALS_PATH) as f:
            credentials = json.load(f)

            code, client_socket = self.get_access_code_and_client(credentials)
        exchange_keys = {
            'client_id': credentials['installed']['client_id'],
            'client_secret': credentials['installed']['client_secret'],
            'code': code,
            'grant_type': 'authorization_code',
            'redirect_uri': 'http://127.0.0.1:8000'

        }
        r = requests.post('https://oauth2.googleapis.com/token',
                          data=exchange_keys)
        expire_time = datetime.datetime.now() + datetime.timedelta(0, r.json()[
            'expires_in'])  # add seconds to current time

        access_token = r.json()['access_token']
        config['token'] = {}
        config['token']['id'] = access_token
        config['token']['expire_time'] = repr(expire_time)

        with open(GOOGLE_TOKEN_PATH, 'w') as configfile:
            config.write(configfile)
        with open(SUCCESS_MESSAGE_PATH) as f:
            message = f'HTTP/1.1 200 OK\r\n\r\n{f.read()}'
        client_socket.send(message.encode())
        return access_token

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

    def create_folder(self, name):
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.gdrive_token}'
        }
        metadata = {'name': name,
                    'mimeType': 'application/vnd.google-apps.folder'}
        r = requests.post('https://www.googleapis.com/drive/v3/files', headers=headers, data=json.dumps(metadata))
        print(r.json())

    def send_initial_request(self, filename, directory, folder=False):
        headers = {
            'Content-type': 'application/json; charset=UTF-8',
            'Authorization': f'Bearer {self.gdrive_token}',
            'X-Upload-Content-Type': mimetypes.guess_type(directory)[0]  # returns tuple (mimetype, encoding)
        }
        metadata = json.dumps({"name": filename})
        r = requests.post('https://www.googleapis.com/upload/drive/v3/files?uploadType=resumable',
                          headers=headers, data=metadata)
        Response = namedtuple('Response', ['resumable_uri', 'headers'])
        return Response(r.headers['location'], headers)

    def single_request_upload_file(self, storage, filename, file_size, directory, zip=False):
        response = self.send_initial_request(filename, directory)
        r = requests.put(response.resumable_uri, data=open(directory, 'rb').read(), headers=response.headers)
        print(r.status_code)

    def multipart_request_upload_file(self, storage, filename, file_size, directory, zip=False):
        response = self.send_initial_request(filename, directory)
        CHUNK_SIZE = 10 * 256 * 1024
        headers = response.headers
        uploaded_size = 0
        with open(directory, 'rb') as file:
            while uploaded_size < file_size:
                if CHUNK_SIZE > file_size:
                    CHUNK_SIZE = file_size
                if file_size - uploaded_size < CHUNK_SIZE:
                    CHUNK_SIZE = file_size - uploaded_size
                file_data = file.read(CHUNK_SIZE)
                headers['Content-Length'] = str(CHUNK_SIZE)
                headers[
                    'Content-Range'] = f'bytes {str(uploaded_size)}-{str(uploaded_size + CHUNK_SIZE - 1)}/{file_size}'
                r = requests.put(response.resumable_uri, data=file_data, headers=headers)
                uploaded_size += CHUNK_SIZE
                if r.status_code == 200:
                    print('Uploaded successfully')
                    return
                file.seek(int(r.headers['range'].split('-')[1]))  # range header looks like start-end
