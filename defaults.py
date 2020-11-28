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

GDRIVE_DIRECTORY_TYPE = "application/vnd.google-apps.folder"
G_SUITE_FILES_TYPE = "application/vnd.google-apps"

CONFIRM_CHOICE_STRING = "([y]/n) "
ABORTED_MSG = "Aborted"
SUCCESSFUL_DOWNLOAD_MSG = "Successfully downloaded file: `{file_name}`"
SUCCESSFUL_UPLOAD_MSG = "Successfully uploaded file: `{file_name}`"
SUCCESSFUL_DELETE_MSG = "Successfully deleted file: `{file_name}`"
SUCCESSFUL_TRASH_MSG = "Successfully moved file: `{file_name}` to the trash"
G_SUITE_DIRECTORY = "Directory: `{file_name}` contains G.Suite file which isn't downloadable. " \
                    "If you want to download directory and skip this file, pass '-f' flag"
G_SUITE_FILE = "G.Suite file: `{file.name}` isn't downloadable."
MOVE_TO_TRASH_CONFIRMATION_MSG = "Are you sure you want to move file: `{file_name}` to the trash? " + CONFIRM_CHOICE_STRING
DELETE_CONFIRMATION_MSG = "Are you sure you want to delete `{file_name}` file? " + CONFIRM_CHOICE_STRING
LIST_NEXT_PAGE_MSG = "List next page? " + CONFIRM_CHOICE_STRING
OVERWRITE_REQUEST_MSG = "Are you sure you want to overwrite file: `{file_name}`? " + CONFIRM_CHOICE_STRING
OVERWRITING_DIRECTORY_MSG = "Overwriting directory: `{dir_name}`..."
OVERWRITING_FILE_MSG = "Overwriting file: `{file_name}`..."
MAKING_DIRECTORY_MSG = "Making directory: `{dir_name}`..."
UPLOADING_DIRECTORY_MSG = "Uploading directory: `{dir_name}`..."
DOWNLOADING_FILE_MSG = "Downloading file: `{file_name}`..."
UPLOADING_FILE_MSG = "Uploading file: `{file_name}`..."
DOWNLOADING_DIR_AS_ZIP_MSG = "Downloading directory: `{dir_name}` as `{file_name}`..."
ACCESS_DENIED_MSG = "No access was granted to overwrite"
SKIP_G_SUITE_FILE_MSG = "Skipping G.Suite file: `{file_name}` ..."
