import unittest
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


class TestGDrive(unittest.TestCase):

    def setUp(self):
        with patch("cloudbackup.gdrive.Authenticator") as MockAuth:
            auth = MockAuth.return_value
            auth.get_gdrive_token.return_value = Mock()
            self.gdrive = GDrive()

    def _default_req_check(self, responses_obj):
        self.assertEqual(1, len(responses_obj.calls))
        self.assertTrue(
            "Authorization" in responses_obj.calls[0].request.headers
        )
        self.assertTrue(
            "Bearer " in responses_obj.calls[0].request.headers["Authorization"]
        )

    def _check_namedtuple_instance(self, obj, fields):
        self.assertIsInstance(obj, tuple)
        self.assertTrue(hasattr(obj, "_fields"))
        #  fields is attribute only of namedtuple
        self.assertEqual(fields[0], obj._fields[0])
        self.assertEqual(fields[1], obj._fields[1])

    @responses.activate
    def test_mkdir(self):
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
        folder_id = self.gdrive.mkdir("test")
        self._default_req_check(responses)
        json_req_body = json.loads(responses.calls[0].request.body)
        self.assertTrue(
            all(key in json_req_body for key in
                ("mimeType", "name", "parents"))
        )
        self.assertListEqual([], json_req_body["parents"])
        self.assertEqual(
            json.loads(responses.calls[0].response.text)["id"],
            folder_id
        )

    @responses.activate
    def test_trash_file(self):
        responses.add(
            responses.POST,
            url="https://www.googleapis.com/drive/v2/files/1/trash",
            content_type="application/json"
        )
        file_id = "1"
        self.gdrive.remove(file_id)
        self._default_req_check(responses)

    @responses.activate
    def test_remove_permanently(self):
        responses.add(
            method="DELETE",
            url="https://www.googleapis.com/drive/v3/files/1",
            content_type="application/json",
        )
        file_id = "1"
        self.gdrive.remove(file_id, permanently=True)
        self._default_req_check(responses)

    @responses.activate
    def test_empty_trash(self):
        #  status code 204, empty text
        responses.add(
            method="DELETE",
            url="https://www.googleapis.com/drive/v3/files/trash",
            content_type="application/json",
            status=204,
        )
        self.gdrive._empty_trash()
        self._default_req_check(responses)
        self.assertEqual(204, responses.calls[0].response.status_code)

    @responses.activate
    def test_lsdir_with_def_args(self):
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
        page = self.gdrive.lsdir()
        self._default_req_check(responses)
        self.assertEqual(
            def_url_params,
            responses.calls[0].request.params
        )
        self._check_namedtuple_instance(page, ["files", "next_page_token"])
        self.assertIsInstance(page.files, list)
        files = [
            GDriveFile(FULL_LISTED_LSDIR_RESPONSE["files"][0]),
            GDriveFile(FULL_LISTED_LSDIR_RESPONSE["files"][1]),
            GDriveFile(FULL_LISTED_LSDIR_RESPONSE["files"][2])
        ]
        self.assertListEqual(files, page.files)
        self.assertIsNone(page.next_page_token)

    @responses.activate
    def test_paginate_lsdir(self):
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
        page = self.gdrive.lsdir(
            page_size=1,
            page_token="some_page_token"
        )
        self._default_req_check(responses)
        self.assertEqual(
            url_params,
            responses.calls[0].request.params
        )
        self._check_namedtuple_instance(page, ["files", "next_page_token"])
        # self.assertIsInstance(page)
        #  нужно ли в каждом тесте проверять что возвращается именно такой тапл?

