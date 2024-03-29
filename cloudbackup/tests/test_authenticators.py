import datetime
import pytest
import pickle
from callee import Contains
from cloudbackup._defaults import (TEST_GOOGLE_TOKEN_PATH,
                                   TEST_YANDEX_TOKEN_PATH)
from cloudbackup._authenticator import Authenticator
from pathlib import Path
from unittest.mock import Mock


@pytest.fixture()
def auth():
    yield Authenticator()
    g_token_path = Path(TEST_GOOGLE_TOKEN_PATH)
    y_token_path = Path(TEST_YANDEX_TOKEN_PATH)
    if g_token_path.exists():
        g_token_path.unlink()
    if y_token_path.exists():
        y_token_path.unlink()


def test_get_gdrive_token_first_time(auth):
    """
    Test GDriveAuth.authenticate method when user have not operated with
    program yet or have deleted token.pickle file.
    """
    auth._client_socket = Mock()
    code = "4/0AY0e-g5asIaMQ1-_XXXXXNcKAel35qh2AjkGGBgAz9_zPXiyzHdw_XXXX"
    auth._handle_user_prompt = Mock(return_value=code)
    token_data = {
        "access_token": "very_secret_access_token",
        "refresh_token": "some_refresh_token",
        "expires_in": 3920,
    }
    auth._get_gdrive_tokens_from_api = Mock(return_value=token_data)
    g_token_path = Path(TEST_GOOGLE_TOKEN_PATH)
    if g_token_path.exists():
        g_token_path.unlink()
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
        auth._get_gdrive_tokens_from_api.assert_called_once_with(
            Contains(keys[i])
        )
    assert get_tokens_args["code"] == code
    assert get_tokens_args["grant_type"] == "authorization_code"
    assert get_tokens_args["redirect_uri"] == "http://127.0.0.1:8000"
    check_dump_token_data(token_data, TEST_GOOGLE_TOKEN_PATH)
    assert access_token == token_data["access_token"]


def test_gdrive_token_extracting_correctly_from_dump(auth):
    """
    Testing case when token file contains not expired token data.
    :return:
    """
    token_data_in_file = {
        "access_token": "very_secret_access_token",
        "refresh_token": "some_refresh_token",
        "expire_time": datetime.datetime.now() + datetime.timedelta(0, 3920)
    }
    with open(TEST_GOOGLE_TOKEN_PATH, "wb") as f:
        pickle.dump(token_data_in_file, f)
    access_token = auth.get_gdrive_token(TEST_GOOGLE_TOKEN_PATH)
    assert access_token == token_data_in_file["access_token"]


def test_gdrive_token_is_refreshed(auth):
    expired_token_data = {
        "access_token": "very_secret_access_token",
        "refresh_token": "some_refresh_token",
        "expire_time": datetime.datetime.now() - datetime.timedelta(0, 100)
    }
    with open(TEST_GOOGLE_TOKEN_PATH, "wb") as f:
        pickle.dump(expired_token_data, f)
    updated_token_data = {
        "refresh_token": expired_token_data["refresh_token"],
        "access_token": "another_secret_access_token",
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
    auth._client_socket = Mock()
    code = "7905534"
    auth._handle_user_prompt = Mock(return_value=code)
    token_data = {
        "access_token": "very_secret_access_token",
        "refresh_token": "some_refresh_token",
        "expires_in": 31466940,
    }
    auth._get_yadisk_tokens_from_api = Mock(return_value=token_data)
    y_token_path = Path(TEST_YANDEX_TOKEN_PATH)
    if y_token_path.exists():
        y_token_path.unlink()
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
        "access_token": "very_secret_access_token",
        "refresh_token": "some_refresh_token",
        "expire_time": datetime.datetime.now() + datetime.timedelta(
            0, 31466940)
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
