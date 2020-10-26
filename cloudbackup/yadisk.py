import webbrowser
import requests
from getpass import getpass


class YaDisk:
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
