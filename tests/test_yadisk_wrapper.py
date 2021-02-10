from pathlib import Path

import pytest
from unittest.mock import Mock, call, patch
from yadisk_wrapper import YaDiskWrapper


@pytest.fixture()
def wrapper():
    with patch("yadisk_wrapper.YaDisk"):
        yield YaDiskWrapper()


def test_lsdir_prints_all_files_if_path_is_none(wrapper, capsys):
    files = [Mock() for _ in range(5)]
    for file in files:
        file.str_value.return_value = files.index(file)
    wrapper._storage.list_files = Mock(side_effect=[files])
    wrapper.lsdir(None, "modified")
    captured = capsys.readouterr()
    assert captured.out == "0\n1\n2\n3\n4\n"


def test_lsdir_calls_list_files_if_path_is_none(wrapper):
    wrapper._storage.list_files = Mock(return_value=[])
    wrapper.lsdir(None, "modified")
    assert wrapper._storage.list_files.mock_calls == [
        call(
            limit=1000,
            sort="modified",
            offset=0
        )
    ]


def test_lsdir_asks_user_if_path_is_given(wrapper, capsys):
    wrapper._storage.lsdir = Mock(
        side_effect=[
            [Mock() for _ in range(5)], [Mock() for _ in range(5)], [], []
        ]
    )
    with patch("builtins.input") as input_mock:
        input_mock.return_value = "y"
        wrapper.lsdir("disk:/random_path", "modified")
        assert input_mock.mock_calls == [
            call("List next page? ([y]/n) ")
        ]


def test_lsdir_calls_lsdir_if_path_is_given(wrapper):
    wrapper._storage.lsdir = Mock(
        side_effect=[
            [Mock()], []
        ]
    )
    wrapper.lsdir("disk:/any_path", "modified")
    assert wrapper._storage.lsdir.mock_calls == [
        call(
            "disk:/any_path",
            limit=20,
            offset=0,
            sort="modified"
        ),
        call(
            "disk:/any_path",
            limit=20,
            offset=20,
            sort="modified"
        )
    ]


def test_upload_calls_put_file_with_disk_prefix(
        wrapper, not_existing_file, not_existing_dir
):
    not_existing_file.touch()
    wrapper._put_file = Mock()
    wrapper.upload(not_existing_file, "/")
    assert wrapper._put_file.mock_calls == [
        call(
            local_path=not_existing_file,
            destination=f"disk:/{not_existing_file.name}"
        )
    ]
    wrapper._put_file.reset_mock()
    not_existing_dir.mkdir()
    inner_file = not_existing_dir / "inner_file.txt"
    inner_file.touch()
    wrapper.upload(not_existing_dir, "/")
    assert wrapper._put_file.mock_calls == [
        call(
            local_path=inner_file,
            destination=f"disk:/{not_existing_dir.name}/inner_file.txt"
        )
    ]


def test_upload_raises_file_not_found(wrapper, tmp_path):
    not_existing_file = tmp_path / "unknown"
    with pytest.raises(FileNotFoundError):
        wrapper.upload(not_existing_file, "root")


def test_upload_puts_file(wrapper, tmp_path):
    existing_file = tmp_path / "testfile.txt"
    existing_file.touch()
    wrapper._put_file = Mock()
    wrapper.upload(existing_file, "/")
    assert wrapper._put_file.mock_calls == [
        call(
            local_path=existing_file,
            destination=f"disk:/{existing_file.name}"
        )
    ]


def test_uploads_handles_complex_dir(wrapper):
    """
    Unreal to test due to Path.iterdir() arbitrary order.
    """
    pass


def test_download_creates_correct_local_filename(wrapper, not_existing_file):
    wrapper._storage.get_download_link = Mock(return_value="random link")
    wrapper._storage.download = Mock(return_value=b"file bytes on remote")
    file = Mock()
    file.type = "file"
    file.id = f"disk:/{not_existing_file.name}"
    wrapper.download(file, ".")
    assert not_existing_file.exists()
    assert not_existing_file.read_bytes() == b"file bytes on remote"


def test_download_file_prints_correct_inf(wrapper, not_existing_file, capsys):
    wrapper._storage.get_download_link = Mock()
    wrapper._storage.download = Mock(return_value=b"any bytes")
    file = Mock()
    file.type = "file"
    file.id = f"disk:/{not_existing_file.name}"
    wrapper.download(file, ".")
    captured = capsys.readouterr()
    assert captured.out == f"Downloading: `{not_existing_file}`...\n"
