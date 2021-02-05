# Cloud Backup

Author: Dmitry Podaruev (ddqof.vvv@gmail.com)

## Description

It's simple tool for backing your data up on Google Drive and Yandex.Disk cloud storages.

## Requirements

See `requirements.txt`

## Examples of usage

### List

Directories marked as `[D]`, files marked as `[F]`, G.Suite files marked as 
`[S]` in CLI output.

#### GDrive

* `./main.py gdrive ls` to list entire content (including directories and files).
* `./main.py gdrive ls root` to list content in directory that has `root` id.


#### YaDisk

* `./main.py yadisk ls` to list all files on storage (excluding directories).
* `./main.py yadisk ls disk:/home` to list content in `/home` directory.


### Upload

#### GDrive

* `./main.py gdrive ul /home/user root` to upload directory `/home/user` to
 `root` directory.
 
* `./main.py gdrive /home/user/test.py root` to upload `test.py` file to
 `root` directory.
 
#### YaDisk

* `./main.py yadisk ul disk:/home/user /` to upload directory `/home/user` to
 `/` directory.
 
* `./main.py yadisk disk:/home/user/test.py /` to upload `test.py` file to
 `/` directory.
 
 
### Download

#### GDrive

Note that G.Suite `[S]` files are not downloadable and you will see only
`Skiping: file_name ...` when you will try to download this G.Suite file 
called `file_name`.

* `./main.py gdrive dl 1n7bDl79J3xf3E2JEENtYqb7nvSdkFof4l .` to download file
 that has id `1n7bDl79J3xf3E2JEENtYqb7nvSdkFof4` in current working directory

* `./main.py yadisk dl disk:/yadisk/path .` to download file located at 
`/yadisk/path` to current working directory.


### Delete

#### GDrive

* `./main.py gdrive rm 1n7bDl79J3xf3E2JEENtYqb7nvSdkFof4l` to move file that
has id `1n7bDl79J3xf3E2JEENtYqb7nvSdkFof4l` to the Trash.
 
* `./main.py gdrive rm 1n7bDl79J3xf3E2JEENtYqb7nvSdkFof4l -p` to permanently
delete file that has provided id.
 
#### YaDisk

* `./main.py yadisk rm disk:/yadisk/path` to move file located at 
`/yadisk/path` to the trash.
* `./main.py yadisk rm -p disk:/yadisk/path` to permanently delete 
file located at `/yadisk/path`.

#### Trick for *nix users
To extract file id you can pipe output of `main.py` like this:

`./main.py gdrive ls | awk 'NR==1' | awk '{print $3}' | tr -d "()"`.

`NR` is number of line where you want to extract ID. You don't
need to change anything else in this commands.
