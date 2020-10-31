import json
import os
import mimetypes
import datetime
import re
import socket
import webbrowser
import requests
import configparser
from urllib.parse import urlencode
from .defaults import (GOOGLE_CREDENTIALS_PATH, GOOGLE_TOKEN_PATH,
                       SUCCESS_MESSAGE_PATH, REDIRECT_HOST, REDIRECT_PORT)


class GDrive:
    def __init__(self):
        self.token = self._authenticate()

    def _authenticate(self):
        config = configparser.ConfigParser()
        if self._token_is_valid(config):
            return config['token']['id']
        with open(GOOGLE_CREDENTIALS_PATH) as f:
            credentials = json.load(f)
            code, client_socket = self._get_access_code_and_client(credentials)
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

    def _token_is_valid(self, config):
        if os.path.exists(GOOGLE_TOKEN_PATH):
            config.read(GOOGLE_TOKEN_PATH)
            if config['token']['expire_time'] != '0':
                expire_time = eval(config['token']['expire_time'])
                if datetime.datetime.now() < expire_time:
                    return True
        return False

    def _get_access_code_and_client(self, credentials):
        keys = {'client_id': credentials['installed']['client_id'],
                'redirect_uri': REDIRECT_HOST + ':' + str(REDIRECT_PORT),
                'response_type': 'code',
                'scope': 'https://www.googleapis.com/auth/drive.file'}
        login_url = 'https://accounts.google.com/o/oauth2/v2/auth?' + urlencode(keys)
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind(('localhost', REDIRECT_PORT))
        s.listen()
        webbrowser.open(login_url)
        client, addr = s.accept()
        response = client.recv(1024).decode()
        return re.search('code=(.*)?&', response).group(1), client

    def create_folder(self, name, parent_id=None):
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.token}'
        }
        metadata = {'name': name,
                    'mimeType': 'application/vnd.google-apps.folder',
                    'parents': [parent_id]}
        r = requests.post('https://www.googleapis.com/drive/v3/files',
                          headers=headers, data=json.dumps(metadata))
        return r.json()['id']

    def _send_initial_request(self, file_path, parent_id=None):
        filename = os.path.basename(file_path)
        headers = {
            'Content-type': 'application/json; charset=UTF-8',
            'Authorization': f'Bearer {self.token}',
            'X-Upload-Content-Type': mimetypes.guess_type(file_path)[0]
            # returns tuple (mimetype, encoding)
        }
        metadata = {"name": filename}
        if parent_id is not None:
            metadata['parents'] = [parent_id]
        metadata = json.dumps(metadata)
        r = requests.post('https://www.googleapis.com/upload/drive/v3/files?uploadType=resumable',
                          headers=headers, data=metadata)
        return r

    def single_upload(self, file_path, parent_id=None):
        response = self._send_initial_request(file_path, parent_id)
        resumable_uri = response.headers['location']
        r = requests.put(resumable_uri, data=open(file_path, 'rb').read(),
                         headers=response.headers)
        print(r.status_code)

    def multipart_upload(self, file_path, parent_id=None):
        file_size = os.path.getsize(file_path)
        response = self._send_initial_request(file_path, parent_id)
        CHUNK_SIZE = 256 * 1024
        headers = response.headers
        resumable_uri = headers['location']
        uploaded_size = 0
        with open(file_path, 'rb') as file:
            while uploaded_size < file_size:
                if CHUNK_SIZE > file_size:
                    CHUNK_SIZE = file_size
                if file_size - uploaded_size < CHUNK_SIZE:
                    CHUNK_SIZE = file_size - uploaded_size
                file_data = file.read(CHUNK_SIZE)
                headers['Content-Length'] = str(CHUNK_SIZE)
                headers[
                    'Content-Range'] =\
                    f'bytes {str(uploaded_size)}-{str(uploaded_size + CHUNK_SIZE - 1)}/{file_size}'
                r = requests.put(resumable_uri, data=file_data, headers=headers)
                uploaded_size += CHUNK_SIZE
                print(r.status_code)
                if r.status_code == 200:
                    print('Uploaded successfully')
                    return
                diff = int(r.headers['range'].split('-')[1]) + 1 - uploaded_size
                # range header looks like "bytes=0-n", where n - received bytes
                file.seek(diff, 1)  # second parameter means seek relative to the current position
