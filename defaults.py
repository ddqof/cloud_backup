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
OW_ACCESS_DENIED_MSG = "No access was granted to overwrite"
RM_ACCESS_DENIED_MSG = "No access was granted to delete"

UPLOAD_COMPLETED_MSG = "Upload completed."
DOWNLOAD_COMPLETED_MSG = "Download completed."
SUCCESSFUL_DOWNLOAD_MSG = "Successfully downloaded `{}`"
SUCCESSFUL_UPLOAD_MSG = "Successfully uploaded `{}`"
SUCCESSFUL_DELETE_MSG = "Successfully deleted  `{}`"
SUCCESSFUL_TRASH_MSG = "Successfully moved `{}` to the trash"

G_SUITE_FILE = "[S]: `{}` isn't downloadable."

MOVE_TO_TRASH_CONFIRMATION_MSG = (
        "Are you sure you want to move `{}` to the trash? " +
        CONFIRM_CHOICE_STRING
)
DELETE_CONFIRMATION_MSG = (
        "Are you sure you want to permanently delete `{}`? " +
        CONFIRM_CHOICE_STRING
)

LIST_NEXT_PAGE_MSG = "List next page? " + CONFIRM_CHOICE_STRING

OVERWRITE_REQUEST_MSG = (
        "Are you sure you want to overwrite `{}`? " +
        CONFIRM_CHOICE_STRING
)
OVERWRITING_MSG = "Overwriting: `{}`..."

UPLOADING_MSG = "Uploading: `{}`..."
DOWNLOADING_MSG = "Downloading: `{}`..."
DOWNLOADING_AS_ZIP_MSG = "Downloading: `{}` as `{}`..."
SKIPPING_MSG = "Skipping: `{}` ..."
