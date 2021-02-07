import mimetypes
from pathlib import Path

import pytest
import json
from unittest.mock import patch, Mock
from urllib.parse import urlencode
import responses
from cloudbackup.exceptions import (
    ApiResponseException,
    FileIsNotDownloadableException
)
from cloudbackup.yadisk import YaDisk
from cloudbackup.file_objects import YaDiskFile
from cloudbackup.tests.test_gdrive import _check_namedtuple_instance
from cloudbackup.tests._yadisk_api_responses import (
    LSDIR_RESPONSE,
    LIST_FILES_RESPONSE
)


@pytest.fixture()
def yadisk():
    with patch("cloudbackup.yadisk.Authenticator") as MockAuth:
        auth = MockAuth.return_value
        auth.get_yadisk_token.return_value = str(Mock())
        yield YaDisk()


@responses.activate
def test_lsdir_def_args(yadisk):
    url_params = {
        "path": "/",
        "sort": "modified",
        "limit": "20",
        "offset": "0",
    }
    responses.add(
        responses.GET,
        url=f"https://cloud-api.yandex.net/v1/disk/resources/?"
            f"{urlencode(url_params)}",
        content_type="application/json",
        match_querystring=True,
        body=json.dumps(LSDIR_RESPONSE),
    )
    yadisk.lsdir("/")
    assert len(responses.calls) == 1
    assert "Authorization" in responses.calls[0].request.headers
    assert responses.calls[0].request.params == url_params


@responses.activate
def test_lsdir_diff_args(yadisk):
    url_params = {
        "path": "/",
        "sort": "path",
        "limit": "10",
        "offset": "5",
    }
    responses.add(
        responses.GET,
        url=f"https://cloud-api.yandex.net/v1/disk/resources/?"
            f"{urlencode(url_params)}",
        content_type="application/json",
        match_querystring=True,
        body=json.dumps(LSDIR_RESPONSE),
    )
    yadisk.lsdir(
        path="/",
        sort="path",
        limit=10,
        offset=5
    )
    assert len(responses.calls) == 1
    assert "Authorization" in responses.calls[0].request.headers
    assert responses.calls[0].request.params == url_params


@responses.activate
def test_lsdir_returns_page(yadisk):
    url_params = {
        "path": "/",
        "sort": "modified",
        "limit": "20",
        "offset": "0",
    }
    responses.add(
        responses.GET,
        url=f"https://cloud-api.yandex.net/v1/disk/resources/?"
            f"{urlencode(url_params)}",
        content_type="application/json",
        match_querystring=True,
        body=json.dumps(LSDIR_RESPONSE),
    )
    dir_page = yadisk.lsdir("/")
    _check_namedtuple_instance(dir_page, ["file_info", "files"])
    assert isinstance(dir_page.file_info, YaDiskFile)
    test_file = YaDiskFile(LSDIR_RESPONSE)
    assert dir_page.file_info == test_file
    assert isinstance(dir_page.files, list)
    files = [
        YaDiskFile(LSDIR_RESPONSE["_embedded"]["items"][0]),
        YaDiskFile(LSDIR_RESPONSE["_embedded"]["items"][1]),
    ]
    assert dir_page.files == files
    url_params["path"] = "/second_file.pdf"
    responses.add(
        responses.GET,
        url=f"https://cloud-api.yandex.net/v1/disk/resources/?"
            f"{urlencode(url_params)}",
        content_type="application/json",
        match_querystring=True,
        body=json.dumps(LSDIR_RESPONSE["_embedded"]["items"][1]),
    )
    file_page = yadisk.lsdir("/second_file.pdf")
    _check_namedtuple_instance(dir_page, ["file_info", "files"])
    assert isinstance(file_page.file_info, YaDiskFile)
    test_file = YaDiskFile(LSDIR_RESPONSE["_embedded"]["items"][1])
    assert file_page.file_info == test_file
    assert isinstance(file_page.files, list)
    assert file_page.files == []


@responses.activate
def test_list_files_def_args(yadisk):
    url_keys = {
        "sort": "name",
        "limit": "20",
        "offset": "0",
    }
    responses.add(
        responses.GET,
        url=f"https://cloud-api.yandex.net/v1/disk/resources/files?"
            f"{urlencode(url_keys)}",
        content_type="application/json",
        match_querystring=True,
        body=json.dumps(LIST_FILES_RESPONSE)
    )
    yadisk.list_files()
    assert len(responses.calls) == 1
    assert "Authorization" in responses.calls[0].request.headers
    assert responses.calls[0].request.params == url_keys


@responses.activate
def test_list_files_diff_args(yadisk):
    url_keys = {
        "sort": "created",
        "limit": "10",
        "offset": "4",
    }
    responses.add(
        responses.GET,
        url=f"https://cloud-api.yandex.net/v1/disk/resources/files?"
            f"{urlencode(url_keys)}",
        content_type="application/json",
        match_querystring=True,
        body=json.dumps(LIST_FILES_RESPONSE)
    )
    yadisk.list_files(
        sort="created",
        limit=10,
        offset=4,
    )
    assert len(responses.calls) == 1
    assert "Authorization" in responses.calls[0].request.headers
    assert responses.calls[0].request.params == url_keys


@responses.activate
def test_list_files_returns_correct_list(yadisk):
    url_keys = {
        "sort": "name",
        "limit": "20",
        "offset": "0",
    }
    responses.add(
        responses.GET,
        url=f"https://cloud-api.yandex.net/v1/disk/resources/files?"
            f"{urlencode(url_keys)}",
        content_type="application/json",
        match_querystring=True,
        body=json.dumps(LIST_FILES_RESPONSE)
    )
    listed_files = yadisk.list_files()
    test_files = [
        YaDiskFile(LIST_FILES_RESPONSE["items"][0]),
        YaDiskFile(LIST_FILES_RESPONSE["items"][1])
    ]  # this list is sorted
    assert listed_files == test_files


@responses.activate
def test_get_download_link(yadisk):
    path = "/tests.txt"
    url_keys = {"path": path}
    responses.add(
        responses.GET,
        url=f"https://cloud-api.yandex.net/v1/disk/resources/download?"
            f"{urlencode(url_keys)}",
        content_type="application/json",
        match_querystring=True,
        json={"href": "https://very_secret_download_ref"}
    )
    download_link = yadisk.get_download_link(path)
    assert len(responses.calls) == 1
    assert "Authorization" in responses.calls[0].request.headers
    assert responses.calls[0].request.params == url_keys
    assert "href" in responses.calls[0].response.json()
    assert responses.calls[0].response.json()["href"] == download_link


@responses.activate
def test_download(yadisk):
    download_link = "https://download_link"
    responses.add(
        responses.GET,
        url=download_link,
        body="raz dva tri\n"
    )
    file_bytes = yadisk.download(download_link)
    assert len(responses.calls) == 1
    assert responses.calls[0].response.content == file_bytes


@responses.activate
def test_move_to_trash(yadisk):
    path = "/remove.txt"
    url_keys = {
        "path": path,
        "permanently": "False"
    }
    responses.add(
        method="DELETE",
        url=f"https://cloud-api.yandex.net/v1/disk/resources?"
            f"{urlencode(url_keys)}",
        content_type="application/json",
        status=204,
        body="",
    )
    yadisk.remove(path)
    assert len(responses.calls) == 1
    assert "Authorization" in responses.calls[0].request.headers
    assert responses.calls[0].request.params == url_keys


@responses.activate
def test_remove_permanently(yadisk):
    path = "/remove.txt"
    url_keys = {
        "path": path,
        "permanently": "True"
    }
    responses.add(
        method="DELETE",
        url=f"https://cloud-api.yandex.net/v1/disk/resources?"
            f"{urlencode(url_keys)}",
        content_type="application/json",
        status=204,
        body="",
    )
    yadisk.remove(path, True)
    assert len(responses.calls) == 1
    assert "Authorization" in responses.calls[0].request.headers
    assert responses.calls[0].request.params == url_keys


@responses.activate
def test_mkdir(yadisk):
    path = "/test_dir"
    url_keys = {"path": path}
    responses.add(
        responses.PUT,
        url=f"https://cloud-api.yandex.net/v1/disk/resources?"
            f"{urlencode(url_keys)}",
        content_type="application/json",
        status=201,
        body=""
    )
    yadisk.mkdir(path)
    assert len(responses.calls) == 1
    assert "Authorization" in responses.calls[0].request.headers
    assert responses.calls[0].request.params == url_keys


@responses.activate
def test_get_upload_link(yadisk):
    file_path = Path("_yadisk_api_responses.py")
    name = f'"name": "{file_path.name}"'
    mime_type = f'"mime_type": "{mimetypes.guess_type(file_path)[0]}"'
    req_params = {
        "path": "/",
        "fields": "{" + name + ", " + mime_type + "}"
    }
    responses.add(
        responses.GET,
        url=f"https://cloud-api.yandex.net/v1/disk/resources/upload?"
            f"{urlencode(req_params)}",
        content_type="application/json",
        json={"href": "some_upload_link"}
    )
    yadisk.get_upload_link(file_path, "/")
    assert len(responses.calls) == 1
    assert "Authorization" in responses.calls[0].request.headers
    assert responses.calls[0].request.params == req_params


@responses.activate
def test_upload_file(yadisk):
    upload_link = "https://cool_upload_link"
    responses.add(
        responses.PUT,
        url=upload_link,
        content_type="application/json",
        body="",
        status=201,
    )
    yadisk.upload_file(upload_link, b"test_bytes")
    assert len(responses.calls) == 1
    assert responses.calls[0].request.body == b"test_bytes"


@responses.activate
def test_lsdir_exception(yadisk):
    path = "/tests"
    url_keys = {
        "path": path,
        "sort": "modified",
        "limit": "20",
        "offset": "0",
    }
    responses.add(
        responses.GET,
        url=f"https://cloud-api.yandex.net/v1/disk/resources/?"
            f"{urlencode(url_keys)}",
        json={
            "message": "Не удалось найти запрошенный ресурс.",
            "description": "Resource not found.",
            "error": "DiskNotFoundError"
        },
        status=404
    )
    with pytest.raises(ApiResponseException) as api_exc:
        yadisk.lsdir(path)
    assert str(api_exc.value) == "Resource not found."
    assert api_exc.value.status_code == 404


@responses.activate
def test_get_download_link_for_not_existing_file(yadisk):
    path = "/not_existing_file.txt"
    url_keys = {"path": path}
    responses.add(
        responses.GET,
        url=f"https://cloud-api.yandex.net/v1/disk/resources/download?"
            f"{urlencode(url_keys)}",
        json={
            "message": "Не удалось найти запрошенный ресурс.",
            "description": "Resource not found.",
            "error": "DiskNotFoundError"
        },
        status=404
    )
    with pytest.raises(ApiResponseException) as api_exc:
        yadisk.get_download_link(path)
    assert str(api_exc.value) == "Resource not found."
    assert api_exc.value.status_code == 404


@responses.activate
def test_get_download_link_for_not_downloadable_file(yadisk):
    path = "/"
    url_keys = {"path": path}
    responses.add(
        responses.GET,
        url=f"https://cloud-api.yandex.net/v1/disk/resources/download?"
            f"{urlencode(url_keys)}",
        json={"href": ""},
        status=200
    )
    with pytest.raises(FileIsNotDownloadableException) as api_exc:
        yadisk.get_download_link(path)
    assert str(api_exc.value) == f"File: `{path}` isn't downloadable."


@responses.activate
def test_make_existing_dir(yadisk):
    path = "/existing_dir"
    url_keys = {"path": path}
    responses.add(
        responses.PUT,
        url=f"https://cloud-api.yandex.net/v1/disk/resources?"
            f"{urlencode(url_keys)}",
        json={
            "message": "По указанному пути \"/existing_dir\""
                       " уже существует папка с таким именем.",
            "description": "Specified path \"/existing_dir\""
                           " points to existent directory.",
            "error": "DiskPathPointsToExistentDirectoryError"
        },
        status=409
    )
    with pytest.raises(ApiResponseException) as api_exc:
        yadisk.mkdir(path)
    assert str(api_exc.value) == ("Specified path \"/existing_dir\""
                                  " points to existent directory.")
    assert api_exc.value.status_code == 409
