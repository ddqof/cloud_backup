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
ACCESS_DENIED_MSG = "No access was granted to overwrite"
UNEXPECTED_VALUE_MSG = "`{var_name}` has unexpected value: {value}"


UPLOAD_COMPLETED_MSG = "Upload completed."
DOWNLOAD_COMPLETED_MSG = "Download completed."
SUCCESSFUL_DOWNLOAD_FILE_MSG = "Successfully downloaded file: `{file_name}`"
SUCCESSFUL_DOWNLOAD_DIR_MSG = "Successfully downloaded directory: `{dir_name}`"
SUCCESSFUL_UPLOAD_FILE_MSG = "Successfully uploaded file: `{file_name}`"
SUCCESSFUL_UPLOAD_DIR_MSG = "Successfully uploaded directory: `{dir_name}`"
SUCCESSFUL_DELETE_FILE_MSG = "Successfully deleted file: `{file_name}`"
SUCCESSFUL_DELETE_DIR_MSG = "Successfully deleted directory: `{dir_name}`"
SUCCESSFUL_FILE_TRASH_MSG = "Successfully moved file: `{file_name}` to the trash"
SUCCESSFUL_DIR_TRASH_MSG = "Successfully moved directory: `{dir_name}` to the trash"


G_SUITE_DIRECTORY = "Directory: `{file_name}` contains G.Suite file which isn't downloadable. " \
                    "If you want to download directory and skip this file, pass '-f' flag"
G_SUITE_FILE = "G.Suite file: `{file.name}` isn't downloadable."


MOVE_FILE_TO_TRASH_CONFIRMATION_MSG = "Are you sure you want to move file: `{file_name}` to the trash? " + CONFIRM_CHOICE_STRING
MOVE_DIR_TO_TRASH_CONFIRMATION_MSG = "Are you sure you want to move directory: `{dir_name}` to the trash? " + CONFIRM_CHOICE_STRING
DELETE_DIR_CONFIRMATION_MSG = "Are you sure you want to delete directory: `{dir_name}`? " + CONFIRM_CHOICE_STRING
DELETE_FILE_CONFIRMATION_MSG = "Are you sure you want to delete file: `{file_name}`? " + CONFIRM_CHOICE_STRING


LIST_NEXT_PAGE_MSG = "List next page? " + CONFIRM_CHOICE_STRING


OVERWRITE_FILE_REQUEST_MSG = "Are you sure you want to overwrite file: `{file_name}`? " + CONFIRM_CHOICE_STRING
OVERWRITE_DIR_REQUEST_MSG = "Are you sure you want to overwrite directory: `{dir_name}`? " + CONFIRM_CHOICE_STRING
OVERWRITING_DIRECTORY_MSG = "Overwriting directory: `{dir_name}`..."
OVERWRITING_FILE_MSG = "Overwriting file: `{file_name}`..."


MAKING_DIRECTORY_MSG = "Making directory: `{dir_name}`..."
UPLOADING_DIRECTORY_MSG = "Uploading  dir: `{dir_name}`..."
DOWNLOADING_FILE_MSG = "Downloading file: `{file_name}`..."
UPLOADING_FILE_MSG = "Uploading file: `{file_name}`..."
DOWNLOADING_DIR_AS_ZIP_MSG = "Downloading directory: `{dir_name}` as `{file_name}`..."
SKIP_G_SUITE_FILE_MSG = "Skipping G.Suite file: `{file_name}` ..."
