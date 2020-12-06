import datetime
import pytest
import os
import pickle
from callee import Contains
from cloudbackup._defaults import TEST_GOOGLE_TOKEN_PATH, TEST_YANDEX_TOKEN_PATH
from cloudbackup._authenticator import Authenticator
from unittest.mock import Mock, patch


@pytest.fixture()
def auth():
    with patch("test_authenticators.Authenticator"):
        yield Authenticator()
    if os.path.exists(TEST_GOOGLE_TOKEN_PATH):
        os.remove(TEST_GOOGLE_TOKEN_PATH)
    if os.path.exists(TEST_YANDEX_TOKEN_PATH):
        os.remove(TEST_YANDEX_TOKEN_PATH)


def test_get_gdrive_token_first_time(auth):
    """
    Test GDriveAuth.authenticate method when user have not operated with
    program yet or have deleted token.pickle file.
    """
    code = "4/0AY0e-g5asI03WpGd_j_30E_aMQ1-_XXXXXNcKAel35qh2AjkGGBgAz9_zPXiyzHdw_XXXX"
    auth._handle_user_prompt = Mock(return_value=code)
    #  tests data from oauth2 docs
    token_data = {
        "access_token": "1/fFAGRNJru1FTz70BzhT3Zg",
        "refresh_token": "1//xEoDL4iW3cxlI7yDbSRFYNG01kVKM2C-259HOF2aQbI",
        "expires_in": 3920,
    }
    auth._get_gdrive_tokens_from_api = Mock(return_value=token_data)
    if os.path.exists(TEST_GOOGLE_TOKEN_PATH):
        os.remove(TEST_GOOGLE_TOKEN_PATH)
    access_token = auth.get_gdrive_token(TEST_GOOGLE_TOKEN_PATH)
    keys = [
        "client_id",
        "redirect_uri",
        "scope",
        "access_type",
    ]
    handle_prompt_args = auth._handle_user_prompt.call_args.args[0]
    for i in range(len(keys)):
        auth._handle_user_prompt.assert_called_once_with(Contains(keys[i]))
    assert "response_type=code" in handle_prompt_args
    get_tokens_args = auth._get_gdrive_tokens_from_api.call_args.args[0]
    #  call args returns tuple with called args
    keys = [
        "client_id",
        "client_secret",
        "code",
        "grant_type",
        "redirect_uri"
    ]
    for i in range(len(keys)):
        auth._get_gdrive_tokens_from_api.assert_called_once_with(Contains(keys[i]))
    assert get_tokens_args["code"] == code
    assert get_tokens_args["grant_type"] == "authorization_code"
    assert get_tokens_args["redirect_uri"] == "http://127.0.0.1:8000"
    assert token_data == TEST_GOOGLE_TOKEN_PATH
    assert access_token == token_data["access_token"]


def test_gdrive_token_extracting_correctly_from_dump(auth):
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
    access_token = auth.get_gdrive_token(TEST_GOOGLE_TOKEN_PATH)
    assert access_token == token_data_in_file["access_token"]


def test_gdrive_token_is_refreshed(auth):
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
    auth._get_gdrive_tokens_from_api = Mock(return_value=updated_token_data)
    access_token = auth.get_gdrive_token(TEST_GOOGLE_TOKEN_PATH)
    must_have_keys = [
        "client_id",
        "client_secret",
        "grant_type",
        "refresh_token"
    ]
    for i in range(len(must_have_keys)):
        auth._get_gdrive_tokens_from_api.assert_called_once_with(
            Contains(must_have_keys[i])
        )
    assert access_token != expired_token_data["access_token"]
    check_dump_token_data(updated_token_data, TEST_GOOGLE_TOKEN_PATH)
    assert isinstance(access_token, str)
    assert access_token == updated_token_data["access_token"]


def test_get_yadisk_token_first_time(auth):
    code = "7905534"
    auth._handle_user_prompt = Mock(return_value=code)
    token_data = {
        "access_token": "AgAAAAAG5xalAAahrb0bqKqpYEnLsQfIIemKzJc",
        "refresh_token": "1:lvpRBSQ5sq4VTTKh:uXEgde1e4q7YG42i-S8Ar"
                         "0cBbaXQk2ER2XImxmIYTlog4cyB6gUL:QKxHAqbWOSp_zKMv58zumw",
        "expires_in": 31466940,
    }
    auth._get_yadisk_tokens_from_api = Mock(return_value=token_data)
    if os.path.exists(TEST_YANDEX_TOKEN_PATH):
        os.remove(TEST_YANDEX_TOKEN_PATH)
    #  tests data from oauth2 docs
    access_token = auth.get_yadisk_token(TEST_YANDEX_TOKEN_PATH)
    keys = [
        "client_id",
        "response_type"
    ]
    handle_prompt_args = auth._handle_user_prompt.call_args.args[0]
    for i in range(len(keys)):
        auth._handle_user_prompt.assert_called_once_with(
            Contains(keys[i])
        )
    assert "response_type=code" in handle_prompt_args
    get_tokens_args = auth._get_yadisk_tokens_from_api.call_args.args[0]
    #  call args returns tuple with called args
    keys = [
        "client_id",
        "client_secret",
        "code",
        "grant_type",
    ]
    for i in range(len(keys)):
        auth._get_yadisk_tokens_from_api.assert_called_once_with(
            Contains(keys[i])
        )
    assert get_tokens_args["code"] == code
    assert get_tokens_args["grant_type"] == "authorization_code"
    check_dump_token_data(token_data, TEST_YANDEX_TOKEN_PATH)
    assert isinstance(access_token, str)
    assert access_token == token_data["access_token"]


def test_yadisk_token_extracting_correctly_from_dump(auth):
    token_data_in_file = {
        "access_token": "AgAAAAAG5xalAAahrb0bqKqpYEnLsQfIIemKzJc",
        "refresh_token": "1:lvpRBSQ5sq4VTTKh:uXEgde1e4q7YG42i-S8Ar"
                         "0cBbaXQk2ER2XImxmIYTlog4cyB6gUL:QKxHAqbWOSp_zKMv58zumw",
        "expire_time": datetime.datetime.now() + datetime.timedelta(0, 31466940)
    }
    with open(TEST_YANDEX_TOKEN_PATH, "wb") as f:
        pickle.dump(token_data_in_file, f)
    access_token = auth.get_yadisk_token(TEST_YANDEX_TOKEN_PATH)
    assert access_token == token_data_in_file["access_token"]


def check_dump_token_data(test_data, filename):
    with open(filename, "rb") as f:
        actual_data = pickle.load(f)
        assert "access_token" in actual_data
        assert "refresh_token" in actual_data
        assert "expire_time" in actual_data
        assert actual_data["access_token"] == test_data["access_token"]
        assert actual_data["refresh_token"] == test_data["refresh_token"]
        assert isinstance(actual_data["expire_time"], datetime.datetime)
        assert actual_data["expire_time"] > datetime.datetime.now()
