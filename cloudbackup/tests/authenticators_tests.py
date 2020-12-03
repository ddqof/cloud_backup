import datetime
import os
import socket
import pickle
from callee import Contains
from cloudbackup._defaults import TEST_GOOGLE_TOKEN_PATH, TEST_YANDEX_TOKEN_PATH
from cloudbackup._authenticator import Authenticator
from unittest import TestCase
from unittest.mock import Mock
from urllib.parse import urlencode


class TestAuthenticator(TestCase):
    def setUp(self) -> None:
        self.auth = Authenticator()
        self.auth._client_socket = Mock()

    @classmethod
    def tearDownClass(cls):
        if os.path.exists(TEST_GOOGLE_TOKEN_PATH):
            os.remove(TEST_GOOGLE_TOKEN_PATH)
        if os.path.exists(TEST_YANDEX_TOKEN_PATH):
            os.remove(TEST_YANDEX_TOKEN_PATH)

    # def test_local_server(self):
    #     """
    #     Test checks that LocalServer.handle will return correct values if
    #     pass url with particular keys into it.
    #
    #     P.S. I'm not sure that this test is required
    #     """
    #     url_keys = {
    #         "client_id": "624999999999-ged8qvejht3nu7rks93tl78f5q2dhmpp.apps.googleusercontent.com",
    #         "redirect_uri": "http://127.0.0.1:8000",
    #         "response_type": "code",
    #         "scope": "https://www.googleapis.com/auth/drive",
    #         "access_type": "offline",
    #     }
    #     code = "4/0AY0e-g5asI03WpGd_j_30E_aMQ1-_XXXXXNcKAel35qh2AjkGGBgAz9_zPXiyzHdw_XXXX"
    #     client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    #     Authenticator._handle_user_prompt = Mock(return_value=(client_socket, code))
    #     url = "https://accounts.google.com/o/oauth2/v2/auth?" + urlencode(url_keys)
    #     result = Authenticator._handle_user_prompt(url)
    #     self.assertIsInstance(result[0], socket.socket)
    #     self.assertIsInstance(result[1], str)
    #     LocalServer.handle.assert_called_once_with(url)

    def test_get_gdrive_token_first_time(self):
        """
        Test GDriveAuth.authenticate method when user have not operated with
        program yet or have deleted token.pickle file.
        """
        code = "4/0AY0e-g5asI03WpGd_j_30E_aMQ1-_XXXXXNcKAel35qh2AjkGGBgAz9_zPXiyzHdw_XXXX"
        self.auth._handle_user_prompt = Mock(return_value=code)
        #  test data from oauth2 docs
        token_data = {
            "access_token": "1/fFAGRNJru1FTz70BzhT3Zg",
            "refresh_token": "1//xEoDL4iW3cxlI7yDbSRFYNG01kVKM2C-259HOF2aQbI",
            "expires_in": 3920,
        }
        self.auth._get_gdrive_tokens_from_api = Mock(return_value=token_data)
        if os.path.exists(TEST_GOOGLE_TOKEN_PATH):
            os.remove(TEST_GOOGLE_TOKEN_PATH)
        access_token = self.auth.get_gdrive_token(TEST_GOOGLE_TOKEN_PATH)
        keys = [
            "client_id",
            "redirect_uri",
            "scope",
            "access_type",
        ]
        handle_prompt_args = self.auth._handle_user_prompt.call_args.args[0]
        for i in range(len(keys)):
            self.auth._handle_user_prompt.assert_called_once_with(Contains(keys[i]))
        self.assertTrue("response_type=code" in handle_prompt_args)
        get_tokens_args = self.auth._get_gdrive_tokens_from_api.call_args.args[0]
        #  call args returns tuple with called args
        keys = [
            "client_id",
            "client_secret",
            "code",
            "grant_type",
            "redirect_uri"
        ]
        for i in range(len(keys)):
            self.auth._get_gdrive_tokens_from_api.assert_called_once_with(Contains(keys[i]))
        self.assertEqual(get_tokens_args["code"], code)
        self.assertEqual(get_tokens_args["grant_type"], "authorization_code")
        self.assertEqual(get_tokens_args["redirect_uri"], "http://127.0.0.1:8000")
        self.check_dump_token_data(token_data, TEST_GOOGLE_TOKEN_PATH)
        self.assertIsInstance(access_token, str)

    def test_gdrive_token_extracting_correctly_from_dump(self):
        """
        Testing case when token file contains not expired token data.
        :return:
        """
        token_data_in_file = {
            "access_token": "1/fFAGRNJru1FTz70BzhT3Zg",
            "refresh_token": "1//xEoDL4iW3cxlI7yDbSRFYNG01kVKM2C-259HOF2aQbI",
            "expire_time": datetime.datetime.now() + datetime.timedelta(0, 3920)
        }
        with open(TEST_GOOGLE_TOKEN_PATH, "wb") as f:
            pickle.dump(token_data_in_file, f)
        access_token = self.auth.get_gdrive_token(TEST_GOOGLE_TOKEN_PATH)
        self.assertEqual(token_data_in_file["access_token"], access_token)

    def test_gdrive_token_is_refreshed(self):
        expired_token_data = {
            "access_token": "1/fFAGRNJru1FTz70BzhT3Zg",
            "refresh_token": "1//xEoDL4iW3cxlI7yDbSRFYNG01kVKM2C-259HOF2aQbI",
            "expire_time": datetime.datetime.now() - datetime.timedelta(0, 100)
        }
        with open(TEST_GOOGLE_TOKEN_PATH, "wb") as f:
            pickle.dump(expired_token_data, f)
        updated_token_data = {
            "refresh_token": expired_token_data["refresh_token"],
            "access_token": "XXXXXXXXXXXXXXXXXXXXXXX",
            "expires_in": 3920
        }
        self.auth._get_gdrive_tokens_from_api = Mock(return_value=updated_token_data)
        access_token = self.auth.get_gdrive_token(TEST_GOOGLE_TOKEN_PATH)
        must_have_keys = [
            "client_id",
            "client_secret",
            "grant_type",
            "refresh_token"
        ]
        for i in range(len(must_have_keys)):
            self.auth._get_gdrive_tokens_from_api.assert_called_once_with(
                Contains(must_have_keys[i])
            )
        self.assertNotEqual(expired_token_data["access_token"], access_token)
        self.check_dump_token_data(updated_token_data, TEST_GOOGLE_TOKEN_PATH)
        self.assertIsInstance(access_token, str)

    def test_get_yadisk_token_first_time(self):
        code = "7905534"
        self.auth._handle_user_prompt = Mock(return_value=code)
        token_data = {
            "access_token": "AgAAAAAG5xalAAahrb0bqKqpYEnLsQfIIemKzJc",
            "refresh_token": "1:lvpRBSQ5sq4VTTKh:uXEgde1e4q7YG42i-S8Ar"
                             "0cBbaXQk2ER2XImxmIYTlog4cyB6gUL:QKxHAqbWOSp_zKMv58zumw",
            "expires_in": 31466940,
        }
        self.auth._get_yadisk_tokens_from_api = Mock(return_value=token_data)
        if os.path.exists(TEST_YANDEX_TOKEN_PATH):
            os.remove(TEST_YANDEX_TOKEN_PATH)
        #  test data from oauth2 docs
        access_token = self.auth.get_yadisk_token(TEST_YANDEX_TOKEN_PATH)
        keys = [
            "client_id",
            "response_type"
        ]
        handle_prompt_args = self.auth._handle_user_prompt.call_args.args[0]
        for i in range(len(keys)):
            self.auth._handle_user_prompt.assert_called_once_with(Contains(keys[i]))
        self.assertTrue("response_type=code" in handle_prompt_args)
        get_tokens_args = self.auth._get_yadisk_tokens_from_api.call_args.args[0]
        #  call args returns tuple with called args
        keys = [
            "client_id",
            "client_secret",
            "code",
            "grant_type",
        ]
        for i in range(len(keys)):
            self.auth._get_yadisk_tokens_from_api.assert_called_once_with(Contains(keys[i]))
        self.assertEqual(get_tokens_args["code"], code)
        self.assertEqual(get_tokens_args["grant_type"], "authorization_code")
        self.check_dump_token_data(token_data, TEST_YANDEX_TOKEN_PATH)
        self.assertIsInstance(access_token, str)

    def test_yadisk_token_extracting_correctly_from_dump(self):
        token_data_in_file = {
            "access_token": "AgAAAAAG5xalAAahrb0bqKqpYEnLsQfIIemKzJc",
            "refresh_token": "1:lvpRBSQ5sq4VTTKh:uXEgde1e4q7YG42i-S8Ar"
                             "0cBbaXQk2ER2XImxmIYTlog4cyB6gUL:QKxHAqbWOSp_zKMv58zumw",
            "expire_time": datetime.datetime.now() + datetime.timedelta(0, 31466940)
        }
        with open(TEST_YANDEX_TOKEN_PATH, "wb") as f:
            pickle.dump(token_data_in_file, f)
        access_token = self.auth.get_yadisk_token(TEST_YANDEX_TOKEN_PATH)
        self.assertEqual(token_data_in_file["access_token"], access_token)

    def check_dump_token_data(self, test_data, filename):
        with open(filename, "rb") as f:
            actual_data = pickle.load(f)
            self.assertTrue("access_token" in actual_data)
            self.assertTrue("refresh_token" in actual_data)
            self.assertTrue("expire_time" in actual_data)
            self.assertEqual(test_data["access_token"], actual_data["access_token"])
            self.assertEqual(test_data["refresh_token"], actual_data["refresh_token"])
            self.assertIsInstance(actual_data["expire_time"], datetime.datetime)
            self.assertTrue(actual_data["expire_time"] > datetime.datetime.now())
