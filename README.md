# Cloud Backup

Author: Dmitry Podaruev (ddqof.vvv@gmail.com)

## Description

It's simple tool for backing your data up on Google Drive and Yandex.Disk cloud storages.

## Requirements

* see `requirements.txt`

## Examples of usage

### List
* `./main.py -ls` to list all files (directories marked cyan color) on remote storage.
* `./main.py -ls -id root` to list all files in `root` directory

### Upload
* `./main.py -ul -p /home/user` to upload directory `/home/user` to root directory.
* `./main.py -ul -p /home/user/test.py` to upload `test.py` file to root directory.

### Downloading
* `./main.py -dl -id 0xyz` to download file with id starts with `0xyz` in current working directory
* `./main.py -dl -id 0xyz -p /home/user` to download file with id starts with `0xyz` to `/home/user` directory

### Delete
* `./main.py -rm -id 0xyz` to delete file or directory with id starts with `0xyz`. Be careful! It deletes without ability to restore.