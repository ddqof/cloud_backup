import pytest
from pathlib import Path
from unittest.mock import Mock, call, patch

from _base_wrapper import BaseWrapper


@pytest.fixture()
@patch.multiple(BaseWrapper, __abstractmethods__=set())
def wrapper():
    return BaseWrapper(Mock())


def test_put_file(wrapper, tmpdir, capsys):
    test_file = tmpdir.join("test.txt")
    test_file.write_binary(b"hello from test file")
    wrapper._storage.get_upload_link.return_value = "upload link"
    wrapper.put_file(test_file.strpath, "root")
    wrapper._storage.get_upload_link.assert_called_once_with(
        test_file.strpath, "root"
    )
    wrapper._storage.upload_file.assert_called_once_with(
        "upload link", b"hello from test file"
    )
    captured = capsys.readouterr()
    assert captured.out == f"Uploading: `{test_file.strpath}`...\n"


def test_remove(wrapper, capsys):
    file = Mock()
    file.name = "test_file"
    wrapper._storage.get_file.return_value = file
    with patch("builtins.input") as input_mock:
        input_mock.return_value = "y"
        wrapper.remove("some_id", permanently=False)
        wrapper._storage.remove.assert_called_once_with(
            "some_id", permanently=False
        )
        input_mock.assert_called_once_with(
            "Are you sure you want to permanently delete `test_file`? ([y]/n) "
        )
