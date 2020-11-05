# Cloud Backup

Author: Dmitry Podaruev (ddqof.vvv@gmail.com)

## Description

It's simple tool for backing your data up on Google Drive and Yandex.Disk cloud storages.

## Requirements

* see `requirements.txt`

## Usage

For now it only works with Google Drive. So if you just launch, you will operate with your Google Drive storage.
To launch type: `./main.py` and then use unix commands:
* `ls` to list all files on remote storage. Be careful! It deletes without ability to restore.
* `ul filename` to upload file called filename.
* `rm filename` to delete file called filename. 
* `dl filename [path]` for download file called filename to path (if not specified then upload to pwd)
*  `exit` to exit
