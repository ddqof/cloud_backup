# Cloud Backup

Author: Dmitry Podaruev (ddqof.vvv@gmail.com)

## Description

It's simple tool for backing your data up on Google Drive and Yandex.Disk cloud storages.

## Requirements

See `requirements.txt`

## Examples of usage

For working with GoogleDrive files id, type exactly first 5 symbols of displayed id. 
With YaDisk simply type displayed path.

### List
* `./main.py gdrive ls` to list all files (directories marked cyan color) on Google Drive storage.
* `./main.py gdrive ls root` to list all files in `root` directory on Goole Drive storage.
* `./main.py gdrive ls 0xyzl` to list all files in `0xyz` directory on Google Drive storage.
* `./main.py yadisk ls root` to list all files on YaDisk storage excluding directories.
* `./main.py yadisk ls /home` to list all files in `/home` directory on YaDisk storage.


### Upload
* `./main.py gdrive ul /home/user` to upload directory `/home/user` to root directory.
* `./main.py gdrive /home/user/test.py` to upload `test.py` file to root directory.
* same in Yandex Disk case

### Downloading
* `./main.py gdrive dl 0xyzl` to download file with id starts with `0xyz` in current working directory
* `./main.py gdrive dl 0xyzl /home/user` to download file with id starts with `0xyz` to `/home/user` directory
* `./main.py yadisk dl disk:/yadisk/path` to download file located at `/yadisk/path` on Yandex Disk storage.
* `./main.py yadisk dl disk:/yadisk/path /home/user/Downloads` to download file located at
 `/yadisk/path` on Yandex Disk storage to `/home/user/Downloads` directory.


### Delete
* `./main.py gdrive rm 0xyzl` to move file or directory with id starts with `0xyz` to the trash.
* `./main.py gdrive rm -p 0xyzl` to permanently delete file with id starts with `0xyz`. 
* `./main.py yadisk rm disk:/yadisk/path` to move file located at `/yadisk/path` on Yandex Disk storage to the trash.
* `./main.py yadisk rm -p disk:/yadisk/path` to permanently file located at `/yadisk/path` on Yandex Disk storage to the trash.
