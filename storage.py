import json
import re
import socket
import webbrowser
import requests
from getpass import getpass


class RemoteStorage:
    def __init__(self):
        self.gdrive_service = self.google_sign_in()
        self.yandex_token = self.yandex_sign_in()

    def google_sign_in(self):
        with open('service/google/credentials.json') as f:
            creds = json.load(f)
        keys = {'client_id': creds['installed']['client_id'],
                'redirect_uri': 'http://127.0.0.1:8000',
                'response_type': 'code',
                'scope': 'https://www.googleapis.com/auth/drive'}
        login_url = 'https://accounts.google.com/o/oauth2/v2/auth?scope={}' \
                    '&redirect_uri={}&response_type={}&client_id={}'
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind(('127.0.0.1', 8000))
        s.listen()
        webbrowser.open(login_url.format(keys['scope'], keys['redirect_uri'], keys['response_type'], keys['client_id']))
        client, addr = s.accept()
        response = client.recv(1024).decode()
        print(response)
        code = self.extract_code_from_request(response)
        exchange_keys = {
            'client_id': creds['installed']['client_id'],
            'client_secret': creds['installed']['client_secret'],
            'code': code,
            'grant_type': 'authorization_code',
            'redirect_uri': 'http://127.0.0.1:8000'
        }
        r = requests.post('https://oauth2.googleapis.com/token',
                          data=exchange_keys)
        try:
            access_token = r.json()['access_token']
            print(f'got access token: {access_token}')
            with open('service/success_message.html') as f:
                message = f'HTTP/1.1 200 OK\r\n\r\n{f.read()}'
            client.send(message.encode())
        except KeyError:
            with open('service/failure_message.html') as f:
                message = f'HTTP/1.1 200 OK\r\n\r\n{f.read()}'
            client.send(message.encode())

    def extract_code_from_request(self, request):
        return re.search('code=(.*)?&', request).group(1)

    def yandex_sign_in(self):
        try:
            with open('service/yandex/yandex_token.txt') as f:
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

    def upload(self, filename, file_size, date, storage_name):
        if storage_name == 'gdrive':
            r = requests.post('https://www.googleapis.com/upload/drive/v3/files?uploadType=resumable')
            print(r.content)
            if r.status_code == 200:
                location = r.headers['location']
                file_data = {'name': date + ' ' + filename}
                headers = {'Content-Length': file_size}
                upload_request = requests.put(location, data=file_data, headers=headers)
            else:
                print('Got non 200 http repsonse status code')
            print('Successfully backed up to Google Drive')
