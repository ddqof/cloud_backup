import pytest
import responses
import json
from unittest.mock import patch, Mock
from urllib.parse import urlencode
from cloudbackup.gdrive import GDrive
from cloudbackup.file_objects import GDriveFile
from cloudbackup.tests._gdrive_api_responses import (
    OBJECT_CREATED_RESPONSE,
    FULL_LISTED_LSDIR_RESPONSE,
    PAGINATED_LSDIR_RESPONSE
)
from pathlib import Path


@pytest.fixture()
def gdrive():
    with patch("cloudbackup.gdrive.Authenticator") as MockAuth:
        auth = MockAuth.return_value
        auth.get_gdrive_token.return_value = Mock()
        yield GDrive()


def check_auth_headers(headers):
    assert "Authorization" in headers
    assert "Bearer " in headers["Authorization"]


@responses.activate
def test_mkdir(gdrive):
    def request_callback(request):
        data = json.loads(request.body)
        resp_body = OBJECT_CREATED_RESPONSE
        resp_body["mimeType"] = "application/vnd.google-apps.folder"
        resp_body["id"] = 1
        resp_body["name"] = data["name"]
        return 200, {}, json.dumps(resp_body)

    responses.add_callback(
        responses.POST,
        "https://www.googleapis.com/drive/v3/files",
        callback=request_callback,
        content_type="application/json"
    )
    folder_id = gdrive.mkdir("tests")
    assert len(responses.calls) == 1
    check_auth_headers(responses.calls[0].request.headers)
    json_req_body = json.loads(responses.calls[0].request.body)
    assert all(key in json_req_body for key in
               ("mimeType", "name", "parents"))
    assert json_req_body["mimeType"] == "application/vnd.google-apps.folder"
    assert json_req_body["parents"] == []
    assert folder_id == json.loads(responses.calls[0].response.text)["id"]


@responses.activate
def test_trash_file(gdrive):
    responses.add(
        responses.POST,
        url="https://www.googleapis.com/drive/v2/files/1/trash",
        content_type="application/json"
    )
    file_id = "1"
    gdrive.remove(file_id)
    assert len(responses.calls) == 1
    check_auth_headers(responses.calls[0].request.headers)


@responses.activate
def test_remove_permanently(gdrive):
    responses.add(
        method="DELETE",
        url="https://www.googleapis.com/drive/v3/files/1",
        content_type="application/json",
    )
    file_id = "1"
    gdrive.remove(file_id, permanently=True)
    assert len(responses.calls) == 1
    check_auth_headers(responses.calls[0].request.headers)


@responses.activate
def test_non_dir_id_in_lsdir_query(gdrive):
    url_params = {
        "orderBy": "modifiedTime",
        "fields": "files(name, mimeType, id), nextPageToken",
        "pageSize": "20",
        "q": "trashed=False",
    }
    responses.add(
        responses.GET,
        url=f"https://www.googleapis.com/drive/v3/files?"
            f"{urlencode(url_params)}",
        content_type="application/json",
        match_querystring=True,
        body=json.dumps(FULL_LISTED_LSDIR_RESPONSE)
    )
    gdrive.lsdir()
    assert len(responses.calls) == 1
    check_auth_headers(responses.calls[0].request.headers)
    assert responses.calls[0].request.params == url_params
    url_params["q"] = "trashed=False and 'me' in owners"
    responses.add(
        responses.GET,
        url=f"https://www.googleapis.com/drive/v3/files?"
            f"{urlencode(url_params)}",
        content_type="application/json",
        match_querystring=True,
        body=json.dumps(FULL_LISTED_LSDIR_RESPONSE)
    )
    gdrive.lsdir(owners=["me"])
    assert len(responses.calls) == 2
    check_auth_headers(responses.calls[1].request.headers)
    assert responses.calls[1].request.params == url_params


@responses.activate
def test_dir_id_in_lsdir_query(gdrive):
    url_params = {
        "orderBy": "modifiedTime",
        "fields": "files(name, mimeType, id), nextPageToken",
        "pageSize": "20",
        "q": "trashed=False and 'root' in parents and 'me' in owners",
    }
    responses.add(
        responses.GET,
        url=f"https://www.googleapis.com/drive/v3/files?"
            f"{urlencode(url_params)}",
        content_type="application/json",
        match_querystring=True,
        body=json.dumps(PAGINATED_LSDIR_RESPONSE)
    )
    gdrive.lsdir(dir_id="root", owners=["me"])
    assert len(responses.calls) == 1
    check_auth_headers(responses.calls[0].request.headers)
    assert responses.calls[0].request.params == url_params
    url_params["q"] = "trashed=False and 'root' in parents"
    responses.add(
        responses.GET,
        url=f"https://www.googleapis.com/drive/v3/files?"
            f"{urlencode(url_params)}",
        content_type="application/json",
        match_querystring=True,
        body=json.dumps(PAGINATED_LSDIR_RESPONSE)
    )
    gdrive.lsdir(dir_id="root")
    assert len(responses.calls) == 2
    check_auth_headers(responses.calls[1].request.headers)
    assert responses.calls[1].request.params == url_params


@responses.activate
def test_paginate_lsdir(gdrive):
    url_params = {
        "orderBy": "modifiedTime",
        "fields": "files(name, mimeType, id), nextPageToken",
        "pageSize": "1",
        "q": "trashed=False",
        "pageToken": "some_page_token"
    }
    responses.add(
        responses.GET,
        url=f"https://www.googleapis.com/drive/v3/files?"
            f"{urlencode(url_params)}",
        content_type="application/json",
        match_querystring=True,
        body=json.dumps(PAGINATED_LSDIR_RESPONSE)
    )
    gdrive.lsdir(
        page_size=1,
        page_token="some_page_token"
    )
    assert len(responses.calls) == 1
    check_auth_headers(responses.calls[0].request.headers)
    assert responses.calls[0].request.params == url_params


@responses.activate
def test_lsdir_returns_page(gdrive):
    url_params = {
        "orderBy": "modifiedTime",
        "fields": "files(name, mimeType, id), nextPageToken",
        "pageSize": "20",
        "q": "trashed=False",
    }
    responses.add(
        responses.GET,
        url=f"https://www.googleapis.com/drive/v3/files?"
            f"{urlencode(url_params)}",
        content_type="application/json",
        match_querystring=True,
        body=json.dumps(FULL_LISTED_LSDIR_RESPONSE)
    )
    page = gdrive.lsdir()
    _check_namedtuple_instance(page, ["files", "next_page_token"])
    assert isinstance(page.files, list)
    files = [
        GDriveFile(FULL_LISTED_LSDIR_RESPONSE["files"][0]),
        GDriveFile(FULL_LISTED_LSDIR_RESPONSE["files"][1]),
        GDriveFile(FULL_LISTED_LSDIR_RESPONSE["files"][2])
    ]
    assert page.files == files
    assert page.next_page_token is None
    responses.replace(
        responses.GET,
        url=f"https://www.googleapis.com/drive/v3/files?"
            f"{urlencode(url_params)}",
        content_type="application/json",
        match_querystring=True,
        body=json.dumps(PAGINATED_LSDIR_RESPONSE)
    )
    other_page = gdrive.lsdir()
    _check_namedtuple_instance(other_page, ["files", "next_page_token"])
    assert isinstance(other_page.files, list)
    files = [
        GDriveFile(PAGINATED_LSDIR_RESPONSE["files"][0]),
        GDriveFile(PAGINATED_LSDIR_RESPONSE["files"][1]),
    ]
    assert other_page.files == files
    assert other_page.next_page_token == "some_next_page_token"


def _check_namedtuple_instance(obj, fields):
    assert isinstance(obj, tuple)
    assert hasattr(obj, "_fields")
    #  fields is attribute only of namedtuple
    assert fields[0] == obj._fields[0]
    assert fields[1] == obj._fields[1]


@responses.activate
def test_download(gdrive):
    responses.add(
        responses.GET,
        url="https://www.googleapis.com/drive/v3/files/1?alt=media",
        match_querystring=True,
        body="one two three\n",
        content_type="application/json",
    )
    result = gdrive.download("1")
    assert len(responses.calls) == 1
    check_auth_headers(responses.calls[0].request.headers)
    assert responses.calls[0].request.params == {"alt": "media"}
    assert responses.calls[0].response.content == b"one two three\n"
    assert result == responses.calls[0].response.content


@responses.activate
def test_get_upload_link(gdrive):
    responses.add(
        responses.POST,
        url="https://www.googleapis.com/upload/drive/v3/files?"
            "uploadType=resumable",
        content_type="application/json",
        headers={"Location": "https://www.googleapis.com/upload/drive/v3/"
                             "files?uploadType=resumable&upload_id=some_id"}
    )
    file_path = Path("_gdrive_api_responses.py")
    link = gdrive.get_upload_link(file_path)
    assert len(responses.calls) == 1
    check_auth_headers(responses.calls[0].request.headers)
    assert "X-Upload-Content-Type" in responses.calls[0].request.headers
    assert json.loads(responses.calls[0].request.body) == {
        "name": "_gdrive_api_responses.py",
        "parents": ["root"]
    }
    assert "Location" in responses.calls[0].response.headers
    assert responses.calls[0].response.headers != ""
    assert link == responses.calls[0].response.headers["Location"]


@responses.activate
def test_upload_file(gdrive):
    upload_link = "https://www.googleapis.com/upload/drive/v3/" \
                  "files?uploadType=resumable&upload_id=1"
    responses.add(
        responses.PUT,
        url=upload_link,
        content_type="application/json",
    )
    gdrive.upload_file(upload_link, b"tests")
    assert len(responses.calls) == 1
    assert responses.calls[0].request.url == upload_link
    assert responses.calls[0].request.body == b"tests"
