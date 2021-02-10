import pytest
from collections import namedtuple
from pathlib import Path
from unittest.mock import Mock, call, patch
from wrappers.gdrive_wrapper import GDriveWrapper


@pytest.fixture()
def wrapper():
    with patch("wrappers.gdrive_wrapper.GDrive"):
        return GDriveWrapper()


@pytest.fixture()
def dl_page():
    Page = namedtuple("Page", ["files", "next_page_token"])
    files = [Mock() for _ in range(2)]
    for file in files:
        file.id = files.index(file)
        file.type = "file"
        file.name = f"test_file-{files.index(file)}"
    return Page(files, None)


@pytest.fixture()
def ls_pages():
    Page = namedtuple("Page", ["files", "next_page_token"])
    files = [Mock() for _ in range(5)]
    for file in files:
        file.str_value.return_value = files.index(file)
    pages = [
        Page([files[4], files[3]], "first_page_token"),
        Page([files[2], files[1]], "second_page_token"),
        Page([files[0]], None)
    ]
    return pages


def test_lsdir_with_file_id_calls_storage_method_correctly(wrapper):
    page = Mock()
    page.files = []
    page.next_page_token = None
    wrapper._storage.lsdir = Mock(side_effect=[page])
    wrapper.lsdir("some_id", "modified")
    assert wrapper._storage.lsdir.mock_calls == [
        call(
            dir_id="some_id",
            owners=["me"],
            page_size=20,
            order_by="modifiedTime",
            page_token=None
        )
    ]


def test_lsdir_without_file_id_calls_storage_method_correctly(wrapper):
    page = Mock()
    page.files = []
    page.next_page_token = None
    wrapper._storage.lsdir = Mock(side_effect=[page])
    wrapper.lsdir(None, "modified")
    assert wrapper._storage.lsdir.mock_calls == [
        call(
            dir_id=None,
            owners=["me"],
            page_size=1000,
            order_by="modifiedTime",
            page_token=None
        )
    ]


def test_lsdir_with_file_id_prints_correct_data(wrapper, capsys, ls_pages):
    wrapper._storage.lsdir = Mock(side_effect=ls_pages)
    with patch("builtins.input") as input_mock:
        input_mock.side_effect = ["y", "yes", ""]
        wrapper.lsdir("random_id", "modified")
        assert input_mock.mock_calls == [
            call("List next page? ([y]/n) ") for _ in range(2)
        ]
        captured = capsys.readouterr()
        assert captured.out == "4\n3\n2\n1\n0\n"


def test_lsdir_prints_only_one_page_and_aborted_msg_if_user_doesnt_confirm(
        wrapper, ls_pages, capsys
):
    wrapper._storage.lsdir = Mock(side_effect=ls_pages)
    with patch("builtins.input") as input_mock:
        input_mock.return_value = "n"
        wrapper.lsdir("random_id", "modified")
        assert input_mock.mock_calls == [
            call("List next page? ([y]/n) ")
        ]
        captured = capsys.readouterr()
        assert captured.out == "4\n3\nAborted.\n"


def test_lsdir_without_file_id_prints_correct_data(wrapper, capsys, ls_pages):
    wrapper._storage.lsdir = Mock(side_effect=ls_pages)
    with patch("builtins.input") as input_mock:
        wrapper.lsdir(file_id=None, order_key="modified")
        input_mock.assert_not_called()
        captured = capsys.readouterr()
        assert captured.out == "4\n3\n2\n1\n0\n"


def test_download_raises_type_error_when_local_dest_is_none(wrapper):
    with pytest.raises(TypeError):
        wrapper.download(Mock(), None)


def test_download_file_prints_correct_data(capsys, wrapper, not_existing_file):
    remote_target = Mock()
    remote_target.type = "file"
    remote_target.name = not_existing_file.name
    wrapper._storage.download = Mock(return_value=b"any bytes")
    wrapper.download(remote_target, Path("."))
    captured = capsys.readouterr()
    assert captured.out == f"Downloading: `{not_existing_file}`...\n"


def test_download_dir_prints_correct_data(
        capsys, wrapper, not_existing_dir, dl_page
):
    remote_target = Mock()
    remote_target.type = "dir"
    remote_target.name = not_existing_dir.name
    wrapper._storage.download = Mock(return_value=b"hello world")
    wrapper._storage.lsdir.return_value = dl_page
    wrapper.download(remote_target, Path("."))
    captured = capsys.readouterr()
    assert captured.out == (
        f"Downloading: `{not_existing_dir}`...\n"
        f"Downloading: `{Path(not_existing_dir, 'test_file-0')}`...\n"
        f"Downloading: `{Path(not_existing_dir, 'test_file-1')}`...\n"
    )


def is_file_downloaded(path: Path, data: bytes):
    return path.exists() and path.is_file() and path.read_bytes() == data


def test_download_dir_happy_path(capsys, wrapper, not_existing_dir, dl_page):
    remote_target = Mock()
    remote_target.type = "dir"
    remote_target.name = not_existing_dir.name
    wrapper._storage.lsdir.return_value = dl_page
    wrapper._storage.download = Mock(
        side_effect=[b"hello from 0", b"hello from 1"]
    )
    wrapper.download(remote_target, Path("."))
    assert not_existing_dir.exists()
    inner_file_0 = Path(not_existing_dir, "test_file-0")
    inner_file_1 = Path(not_existing_dir, "test_file-1")
    assert is_file_downloaded(inner_file_0, b"hello from 0")
    assert is_file_downloaded(inner_file_1, b"hello from 1")


def test_download_doesnt_overwrite(tmp_path, wrapper, capsys):
    test_file = tmp_path / "testfile.txt"
    testfile_content = b"check that this content will not disappear"
    test_file.write_bytes(testfile_content)
    remote_target = Mock()
    remote_target.name = "testfile.txt"
    with pytest.raises(FileExistsError):
        wrapper.download(remote_target, tmp_path)
        captured = capsys.readouterr()
        assert "File exists: `testfile.txt`" in captured.out
    assert test_file.read_bytes() == testfile_content


def test_download_overwrites(tmp_path, wrapper):
    test_file = tmp_path / "testfile.txt"
    test_file.write_bytes(b"hello from testfile")
    file = Mock()
    file.name = "testfile.txt"
    file.type = "file"
    wrapper._storage.download = Mock(return_value=b"erased data")
    with patch("wrappers.gdrive_wrapper.GdriveDLMessage"):
        wrapper.download(file, tmp_path, ov=True)
        assert test_file.read_bytes() == b"erased data"


def test_upload_file_handles_simple_file_correctly(wrapper, tmp_path):
    wrapper._put_file = Mock()
    test_file = tmp_path / "testfile.txt"
    test_file.touch()
    wrapper.upload(test_file, "root")
    assert wrapper._put_file.mock_calls == [
        call(
            local_path=test_file,
            destination="root"
        )
    ]


def test_upload_resolves_dot_directory(wrapper, tmp_path):
    wrapper._storage.mkdir = Mock()
    wrapper.upload(Path("."), "root")
    assert wrapper._storage.mkdir.mock_calls[0] == call(
        Path(".").resolve().name,
        parent_id="root"
    )


def test_upload_raises_file_not_found_err(wrapper, tmp_path):
    not_existing_file = tmp_path / "not_existing_file.txt"
    with pytest.raises(FileNotFoundError):
        wrapper.upload(not_existing_file, "root")


def test_uploads_handles_complex_dir(wrapper):
    """
    Unreal to test due to Path.iterdir() arbitrary order.
    """
    pass
