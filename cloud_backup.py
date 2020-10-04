#!/usr/bin/env python3

import argparse
import pickle
import zipfile
import os
from datetime import datetime
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.http import MediaFileUpload


class RemoteStorage:
    def __init__(self):
        self.gdrive_service = build('drive', 'v3', credentials=self.google_sign_in())

    def google_sign_in(self):
        # If modifying these scopes, delete the file token.pickle.
        scopes = ['https://www.googleapis.com/auth/drive']
        creds = None
        # The file token.pickle stores the user's access and refresh tokens, and is
        # created automatically when the authorization flow completes for the first
        # time.
        if os.path.exists('token.pickle'):
            with open('token.pickle', 'rb') as token:
                creds = pickle.load(token)
        # If there are no (valid) credentials available, let the user log in.
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    'credentials.json', scopes)
                creds = flow.run_local_server(port=0)
            # Save the credentials for the next run
            with open('token.pickle', 'wb') as token:
                pickle.dump(creds, token)

        return creds

    def upload(self, filename, date, storage_name):
        if storage_name == 'gdrive':
            file_metadata = {'name': date + ' ' + filename}
            media = MediaFileUpload(filename, resumable=True)
            file = self.gdrive_service.files().create(body=file_metadata,
                                                      media_body=media,
                                                      fields='id').execute()


def main():
    args = parse_args()
    storage = RemoteStorage()
    timestamp = str(datetime.now()).split('.')[0]

    filename = args.filename
    if args.filename is None:
        filename = args.dir

    if args.zip:
        zip_directory(args.dir, filename)
        filename = filename + '.zip'

    storage.upload(filename, timestamp, args.storage)

    if os.path.exists(filename):
        os.remove(filename)

    # print('File ID:{}'.format(file.get('id')))
    print('Successfully backed up')


def zip_directory(directory, zip_name):
    with zipfile.ZipFile(zip_name + '.zip', 'w') as zf:
        for root, dirs, files in os.walk(directory):
            for file in files:
                zf.write(os.path.join(root, file))


def parse_args():
    parser = argparse.ArgumentParser(
        usage='[-s] STORAGE_NAME [-d] DIRECTORY [-n] BACKUP_NAME [-z]',
        prog='cloud_backup.py',
        description='''Tool for backing your data up on Google Drive and Yandex.Disk.''',
        epilog='''Author: Dmitry Podaruev <ddqof.vvv@gmail.com>'''
    )
    parser.add_argument('-s', '--storage',
                        metavar='',
                        help='specify remote storage name (examples: gdrive, yadisk)',
                        type=str)
    parser.add_argument('-d', '--dir',
                        metavar='',
                        help='specify directory that you want to back up',
                        type=str)
    parser.add_argument('-f', '--filename',
                        metavar='',
                        help='specify backup name (default: same as the directory)',
                        type=str)
    parser.add_argument('-z', '--zip',
                        help='compress your data using zip',
                        action='store_true')
    return parser.parse_args()


if __name__ == '__main__':
    main()
