import unittest
import json
import secrets
from unittest.mock import patch, Mock
import requests
import responses
import string
from cloudbackup.gdrive import GDrive
from cloudbackup.tests.gdrive_api_responses import (
    MKDIR_RESPONSE
)


class TestGDrive(unittest.TestCase):

    def setUp(self):
        with patch("cloudbackup.gdrive.Authenticator") as MockAuth:
            auth = MockAuth.return_value
            auth.get_gdrive_token.return_value = Mock()
            self.gdrive = GDrive()

    @responses.activate
    def test_mkdir(self):
        def request_callback(request):
            headers = request.headers
            data = json.loads(request.body)
            folder_mime_type = "application/vnd.google-apps.folder"
            if (
                    "Authorization" in headers and
                    "Bearer " in headers["Authorization"] and
                    all(key in data for key in ("mimeType", "name", "parents")) and
                    data["mimeType"] == folder_mime_type and
                    isinstance(data["parents"], list) and
                    isinstance(data["name"], (int, str))
            ):
                # file_id = self.get_random_id(33)
                resp_body = json.loads(MKDIR_RESPONSE)
                resp_body["id"] = 2
                resp_body["name"] = data["name"]
                resp_body["mimeType"] = folder_mime_type
                return 200, {}, json.dumps(resp_body)

        responses.add_callback(
            responses.POST,
            "https://www.googleapis.com/drive/v3/files",
            callback=request_callback,
            content_type="application/json"
        )
        self.gdrive.mkdir("test")
        f = 2

#  подумать над ассертами