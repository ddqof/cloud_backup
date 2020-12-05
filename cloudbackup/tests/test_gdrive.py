import pytest
import json
from unittest.mock import patch, Mock
from urllib.parse import urlencode
import responses
from cloudbackup.gdrive import GDrive
from cloudbackup.file_objects import GDriveFile
from cloudbackup.tests.gdrive_api_responses import (
    MKDIR_RESPONSE,
    FULL_LISTED_LSDIR_RESPONSE,
    PAGINATED_LSDIR_RESPONSE
)


@pytest.fixture()
def gdrive():
    with patch("cloudbackup.gdrive.Authenticator") as MockAuth:
        auth = MockAuth.return_value
        auth.get_gdrive_token.return_value = Mock()
        yield GDrive()


def _default_req_check(responses_obj):
    assert len(responses_obj.calls) == 1
    assert "Authorization" in responses_obj.calls[0].request.headers
    assert "Bearer " in responses_obj.calls[0].request.headers["Authorization"]


def _check_namedtuple_instance(obj, fields):
    assert isinstance(obj, tuple)
    assert hasattr(obj, "_fields")
    #  fields is attribute only of namedtuple
    assert fields[0] == obj._fields[0]
    assert fields[1] == obj._fields[1]


@responses.activate
def test_mkdir(gdrive):
    def request_callback(request):
        data = json.loads(request.body)
        resp_body = MKDIR_RESPONSE
        resp_body["id"] = 1
        resp_body["name"] = data["name"]
        return 200, {}, json.dumps(resp_body)

    responses.add_callback(
        responses.POST,
        "https://www.googleapis.com/drive/v3/files",
        callback=request_callback,
        content_type="application/json"
    )
    folder_id = gdrive.mkdir("test")
    _default_req_check(responses)
    json_req_body = json.loads(responses.calls[0].request.body)
    assert all(key in json_req_body for key in
               ("mimeType", "name", "parents"))
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
    _default_req_check(responses)


@responses.activate
def test_remove_permanently(gdrive):
    responses.add(
        method="DELETE",
        url="https://www.googleapis.com/drive/v3/files/1",
        content_type="application/json",
    )
    file_id = "1"
    gdrive.remove(file_id, permanently=True)
    _default_req_check(responses)


@responses.activate
def test_empty_trash(gdrive):
    #  status code 204, empty text
    responses.add(
        method="DELETE",
        url="https://www.googleapis.com/drive/v3/files/trash",
        content_type="application/json",
        status=204,
    )
    gdrive._empty_trash()
    _default_req_check(responses)
    assert responses.calls[0].response.status_code == 204


@responses.activate
def test_lsdir_with_def_args(gdrive):
    def_url_params = {
        "orderBy": "modifiedTime",
        "fields": "files(name, mimeType, id), nextPageToken",
        "pageSize": "20",
        "q": "trashed=False",
    }
    responses.add(
        responses.GET,
        url=f"https://www.googleapis.com/drive/v3/files?{urlencode(def_url_params)}",
        content_type="application/json",
        match_querystring=True,
        body=json.dumps(FULL_LISTED_LSDIR_RESPONSE)
    )
    page = gdrive.lsdir()
    _default_req_check(responses)
    assert responses.calls[0].request.params == def_url_params
    _check_namedtuple_instance(page, ["files", "next_page_token"])
    assert isinstance(page.files, list)
    files = [
        GDriveFile(FULL_LISTED_LSDIR_RESPONSE["files"][0]),
        GDriveFile(FULL_LISTED_LSDIR_RESPONSE["files"][1]),
        GDriveFile(FULL_LISTED_LSDIR_RESPONSE["files"][2])
    ]
    assert page.files == files
    assert page.next_page_token is None


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
        url=f"https://www.googleapis.com/drive/v3/files?{urlencode(url_params)}",
        content_type="application/json",
        match_querystring=True,
        body=json.dumps(PAGINATED_LSDIR_RESPONSE)
    )
    page = gdrive.lsdir(
        page_size=1,
        page_token="some_page_token"
    )
    _default_req_check(responses)
    assert responses.calls[0].request.params == url_params
    _check_namedtuple_instance(page, ["files", "next_page_token"])
    assert isinstance(page.files, list)
    assert page.next_page_token is not None
    assert page.next_page_token == "some_next_page_token"

