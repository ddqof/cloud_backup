# Cloud Backup

Author: Dmitry Podaruev (ddqof.vvv@gmail.com)

## Description

It's simple tool for backing your data up on Google Drive and Yandex.Disk cloud storages.

## Requirements

* Python 2.6 or greater
* Google Drive API (see `requirements.txt`)

## Usage

Example of usage: `./cloud_backup.py -s REMOTE_STORAGE -d PATH -f BACKUP_NAME -z`
* `PATH` is directory that you want to back up
* `BACKUP_NAME` is name of your future backup in Google Drive
* `REMOTE_STORAGE` is name of remote storage
(if you want to use Google Drive, then type `gdrive`)
* use argument `-z` if you want to compress your folder