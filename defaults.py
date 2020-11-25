GDRIVE_SORT_KEYS = {
        "name": "name",
        "modified": "modifiedTime",
        "created": "createdTime",
        "size": "quotaBytesUsed",
        "folder": "folder",
        "rev_name": "name desc",
        "rev_modified": "modifiedTime desc",
        "rev_created": "createdTime desc",
        "rev_size": "quotaBytesUsed desc",
        "rev_folder": "folder desc",
    }
YADISK_SORT_KEYS = {
    "name": "name",
    "created": "created",
    "modified": "modified",
    "size": "size",
    "path": "rev path",
    "rev_name": "-name",
    "rev_created": "-created",
    "rev_modified": "-modified",
    "rev_size": "-size",
    "rev_path": "-path",
}
CONFIRM_CHOICE_STRING = "([y]/n) "
ABORTED_MSG = "Aborted"
SUCCESSFUL_DOWNLOAD_MSG = "Successfully downloaded file: `{file_name}`"
SUCCESSFUL_UPLOAD_MSG = "Successfully uploaded file: `{file_name}`"
SUCCESSFUL_DELETE_MSG = "Successfully deleted file: `{file_name}`"
SUCCESSFUL_TRASH_MSG = "Successfully moved file: `{file_name}` to the trash"
G_SUITE_DIRECTORY = "Directory: `{file_name}` contains G.Suite file which isn't downloadable. " \
                    "If you want to download directory and skip this file, pass '-f' flag"
G_SUITE_FILE = "G.Suite file: `{file.name}` isn't downloadable."
MOVE_TO_TRASH_CONFIRMATION_MSG = "Are you sure you want to move {file_name} to trash? " + CONFIRM_CHOICE_STRING
DELETE_CONFIRMATION_MSG = "Are you sure you want to delete {file_name} file? " + CONFIRM_CHOICE_STRING
LIST_NEXT_PAGE_MSG = "List next page? " + CONFIRM_CHOICE_STRING
