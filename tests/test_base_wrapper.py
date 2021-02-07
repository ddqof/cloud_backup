import pytest
from unittest.mock import Mock, patch, call
from _base_wrapper import BaseWrapper


@pytest.fixture()
@patch.multiple(BaseWrapper, __abstractmethods__=set())
def wrapper():
    """
    patch.multiple required for being able to initiate abstract class.
    """
    return BaseWrapper(Mock())


@pytest.fixture()
def remote_file():
    file = Mock()
    file.name = "test_file"
    return file


def test_put_file_gets_upload_link_and_then_uploads(wrapper, tmp_path):
    test_file = tmp_path / "test.txt"
    test_file.write_bytes(b"hello from test file")
    wrapper._storage.get_upload_link = Mock(return_value="upload link")
    wrapper._storage.upload_file = Mock()
    wrapper._put_file(test_file, "root")
    assert wrapper._storage.get_upload_link.mock_calls == [
        call(test_file, "root")
    ]
    assert wrapper._storage.upload_file.mock_calls == [
        call("upload link", b"hello from test file")
    ]


def test_remove_prints_correct_data(wrapper, capsys, remote_file):
    wrapper._storage.get_file.return_value = remote_file
    with patch("builtins.input") as input_mock:
        input_mock.return_value = "y"
        wrapper.remove("some_id", permanently=False)
        assert input_mock.mock_calls == [
            call(
                "Are you sure you want to permanently delete "
                "`test_file`? ([y]/n) "
            )
        ]


def test_remove_call_storage_remove_properly(wrapper, remote_file):
    wrapper._storage.get_file.return_value = remote_file
    with patch("builtins.input") as input_mock:
        input_mock.return_value = "y"
        wrapper.remove("some_id", permanently=False)
        assert wrapper._storage.remove.mock_calls == [
            call("some_id", permanently=False)
        ]
