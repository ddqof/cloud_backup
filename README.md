# Cloud Backup

Author: Dmitry Podaruev (ddqof.vvv@gmail.com)

## Description

It's simple tool for backing your data up on Google Drive and Yandex.Disk cloud storages.

## Requirements

* see `requirements.txt`

## Examples of usage

### List
* `./main.py gdrive ls` to list all files (directories marked cyan color) on Google Drive storage.
* `./main.py gdrive ls root` to list all files in `root` directory

Tip: pipe output of `ls` command to `less` unix util for page-view.
For example: `./main.py gdrive ls | less`.

### Upload
* `./main.py gdrive ul /home/user` to upload directory `/home/user` to root directory.
* `./main.py gdrive /home/user/test.py` to upload `test.py` file to root directory.

### Downloading
* `./main.py gdrive dl 0xyz` to download file with id starts with `0xyz` in current working directory
* `./main.py gdrive dl 0xyz /home/user` to download file with id starts with `0xyz` to `/home/user` directory

### Delete
* `./main.py gdrive rm 0xyz` to move file or directory with id starts with `0xyz` to the trash.
* `./main.py gdrive rm -p 0xyz` to permanently delete file with id starts with `0xyz`. 