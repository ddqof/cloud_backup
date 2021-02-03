import pytest
import os
import shutil
from unittest.mock import Mock, call, patch
from gdrive_wrapper import GDriveWrapper
from cloudbackup.gdrive import GDrive


@pytest.fixture()
def wrapper():
    with patch("test_gdrive_wrapper.GDrive"):
        yield GDriveWrapper(GDrive())


def test_get_all_files(wrapper):
    wrapper._gdrive.lsdir = Mock()
    wrapper._gdrive.lsdir.side_effect = [
        ([6, 5], "first_page_token"),
        ([4, 3], "second_page_token"),
        ([2, 1], None)
    ]
    result = wrapper.get_all_files(owners=["me"])
    assert wrapper._gdrive.lsdir.call_count == 3
    calls = [
        call(owners=["me"], page_size=1000, page_token=None),
        call(owners=["me"], page_size=1000, page_token="first_page_token"),
        call(owners=["me"], page_size=1000, page_token="second_page_token")
    ]
    wrapper._gdrive.lsdir.assert_has_calls(
        calls,
        any_order=True
    )
    assert result == [6, 5, 4, 3, 2, 1]


def test_get_file_object_by_id(wrapper):
    wrapper._gdrive.lsdir = Mock()
    mock1, mock2, mock3, mock4 = Mock(), Mock(), Mock(), Mock()
    mock1.id = "12345"
    mock2.id = "24567"
    mock3.id = "85545"
    mock4.id = "50914"
    wrapper._gdrive.lsdir.side_effect = [
        ([mock1, mock2], "first_page_token"),
        ([mock3, mock4], None)
    ]
    result = wrapper.get_file_object_by_id("50")
    assert result == mock4


def test_get_root_object(wrapper):
    result = wrapper.get_file_object_by_id("root")
    assert result.id == "root"


def test_get_file_obj_collision(wrapper):
    wrapper._gdrive.lsdir = Mock()
    mock1, mock2 = Mock(), Mock()
    mock1.id = "12345"
    mock2.id = "12567"
    wrapper._gdrive.lsdir.side_effect = [
        ([mock1, mock2], None),
    ]
    with pytest.raises(FileNotFoundError) as e:
        wrapper.get_file_object_by_id("12")
    assert str(e.value) == "Please enter more symbols to determine File ID."


def test_get_not_existing_file_obj(wrapper):
    wrapper._gdrive.lsdir = Mock()
    mock1, mock2 = Mock(), Mock()
    mock1.id = "12345"
    mock2.id = "12567"
    wrapper._gdrive.lsdir.side_effect = [
        ([mock1, mock2], None),
    ]
    with pytest.raises(FileNotFoundError) as e:
        wrapper.get_file_object_by_id("34")
    assert str(e.value) == "There is no file starts with id: 34."


def test_lsdir_with_wrong_start_id(wrapper):
    wrapper.get_file_object_by_id = Mock(side_effect=FileNotFoundError)
    with patch("gdrive_wrapper.print_remote_file") as \
            print_rf_mock:
        with pytest.raises(FileNotFoundError):
            wrapper.lsdir("not_existing_id", "modified")
        print_rf_mock.assert_not_called()


def test_list_all(wrapper):
    wrapper.get_file_object_by_id = Mock(return_value=None)
    files = [Mock() for _ in range(3)]
    wrapper.get_all_files = Mock(return_value=files)
    with patch("gdrive_wrapper.print_remote_file") as \
            print_rf_mock:
        wrapper.lsdir("some_id", "modified")
        wrapper.get_file_object_by_id.assert_called_once_with("some_id")
        wrapper.get_all_files.assert_called_once_with(owners=["me"])
        assert print_rf_mock.call_count == len(files)
        calls = []
        for i in range(len(files)):
            calls.append(
                call(file_name=files[i].name,
                     file_id=files[i].id,
                     file_type=files[i].type)
            )
        print_rf_mock.assert_has_calls(
            calls,
            any_order=True
        )


def test_list_file(wrapper):
    gdrive_file_mock = Mock()
    gdrive_file_mock.type = "file"
    wrapper.get_file_object_by_id = Mock(return_value=gdrive_file_mock)
    with patch("gdrive_wrapper.print_remote_file") as \
            print_rf_mock:
        wrapper.lsdir("some_id", "modified")
        wrapper.get_file_object_by_id.assert_called_once_with("some_id")
        print_rf_mock.assert_called_once_with(
            file_name=gdrive_file_mock.name,
            file_id=gdrive_file_mock.id,
            file_type=gdrive_file_mock.type
        )


def test_paginated_list(wrapper):
    first_page = Mock()
    first_page.files = [Mock() for _ in range(20)]
    first_page.next_page_token = "first_page_token"

    second_page = Mock()
    second_page.files = [Mock() for _ in range(20)]
    second_page.next_page_token = None

    wrapper._gdrive.lsdir = Mock(
        side_effect=[first_page, second_page]
    )
    print_rf_calls = []
    for i in range(20):
        print_rf_calls.append(
            call(file_name=first_page.files[i].name,
                 file_id=first_page.files[i].id,
                 file_type=first_page.files[i].type)
        )
    for i in range(20):
        print_rf_calls.append(
            call(file_name=second_page.files[i].name,
                 file_id=second_page.files[i].id,
                 file_type=second_page.files[i].type)
        )
    with patch("gdrive_wrapper.print_remote_file") as \
            print_rf_mock:
        with patch("builtins.input") as input_mock:
            gdrive_file_mock = Mock()
            gdrive_file_mock.type = "dir"
            wrapper.get_file_object_by_id = Mock(return_value=gdrive_file_mock)
            lsdir_calls = [
                call(
                    dir_id=gdrive_file_mock.id,
                    owners=["me"],
                    page_size=20,
                    order_by="modifiedTime",
                    page_token=None),
                call(
                    dir_id=gdrive_file_mock.id,
                    owners=["me"],
                    page_size=20,
                    order_by="modifiedTime",
                    page_token="first_page_token"
                )
            ]
            input_mock.return_value = "y"
            wrapper.lsdir("some_id", "modified")
        assert wrapper._gdrive.lsdir.call_count == 2
        wrapper._gdrive.lsdir.assert_has_calls(lsdir_calls)
        print_rf_mock.assert_has_calls(print_rf_calls)


def test_remove(wrapper):
    gdrive_file_mock = Mock()
    wrapper.get_file_object_by_id = Mock(return_value=gdrive_file_mock)
    with patch("gdrive_wrapper.remove_remote_file") as rm_mock:
        wrapper.remove("some_id")
        rm_mock.assert_called_once_with(
            storage=wrapper._gdrive,
            file_name=gdrive_file_mock.name,
            destination=gdrive_file_mock.id,
            file_type=gdrive_file_mock.type,
            permanently=False,
        )


def test_remove_with_wrong_start_id(wrapper):
    wrapper.get_file_object_by_id = Mock(side_effect=FileNotFoundError)
    with patch("gdrive_wrapper.remove_remote_file") as rm_mock:
        with pytest.raises(FileNotFoundError):
            wrapper.remove("not_existing_id")
        rm_mock.assert_not_called()


def test_download_file_with_def_args(capsys, wrapper):
    remote_target = Mock()
    remote_target.type = "file"
    remote_target.name = "testfile"
    remote_target.id = "some_id"
    if os.path.exists(remote_target.name):
        os.remove(remote_target.name)
    wrapper.get_file_object_by_id = Mock(return_value=remote_target)
    wrapper._gdrive.download = Mock(return_value=b"hello world")
    with patch("gdrive_wrapper.print_ow_dialog") as ov_mock:
        wrapper.download(remote_target)
        captured = capsys.readouterr()
        assert captured.out == f"Downloading file:" \
                               f" `{os.path.abspath(remote_target.name)}`...\n"
        ov_mock.assert_not_called()
        assert os.path.exists(remote_target.name)
        with open(remote_target.name, "rb") as f:
            assert f.read() == b"hello world"
        os.remove(remote_target.name)


def test_download_dir_with_def_args(capsys, wrapper):
    remote_target = Mock()
    remote_target.type = "dir"
    remote_target.name = "testdir"
    remote_target.id = "some_id"
    if os.path.exists(remote_target.name):
        shutil.rmtree(remote_target.name)
    wrapper.get_file_object_by_id = Mock(return_value=remote_target)

    first_page = Mock()
    file_1 = Mock()
    file_1.type = "dir"
    file_1.name = "first_inner_dir"
    file_1.id = "first_dir_id"
    file_3 = Mock()
    file_3.type = "file"
    file_3.name = "first_inner_file"
    file_3.id = "second_file_id"
    first_page.files = [file_1, file_3]
    first_page.next_page_token = None

    second_page = Mock()
    file_2 = Mock()
    file_2.type = "file"
    file_2.name = "file_in_first_inner_dir"
    file_2.id = "third_file_id"
    second_page.files = [file_2]
    second_page.next_page_token = None

    def lsdir_effect(file_id, owners, page_token, page_size):
        if file_id == "some_id":
            return first_page
        elif file_id == "first_dir_id":
            return second_page

    def download_effect(file_id):
        if file_id == "second_file_id":
            return b"hello from first inner file"
        elif file_id == "third_file_id":
            return b"hello from file in first inner dir"

    wrapper._gdrive.download = Mock(side_effect=download_effect)
    wrapper._gdrive.lsdir = Mock(side_effect=lsdir_effect)
    wrapper.download(remote_target)
    calls = [
        call(
            "some_id",
            owners=["me"],
            page_token=None,
            page_size=1000,
        ),
        call(
            "first_dir_id",
            owners=["me"],
            page_token=None,
            page_size=1000,
        ),
    ]
    assert wrapper._gdrive.lsdir.call_count == 2
    wrapper._gdrive.lsdir.assert_has_calls(calls)
    captured = capsys.readouterr()
    target_dir = os.path.abspath(remote_target.name)
    inner_dir = os.path.join(target_dir, file_1.name)
    file_in_inner_dir = os.path.join(inner_dir, file_2.name)
    inner_file = os.path.join(target_dir, file_3.name)
    assert os.path.isdir(target_dir)
    assert os.path.isdir(inner_dir)
    assert os.path.isfile(file_in_inner_dir)
    assert os.path.isfile(inner_file)
    with open(file_in_inner_dir, "rb") as f:
        assert f.read() == b"hello from file in" \
                           b" first inner dir"
    with open(inner_file, "rb") as f:
        assert f.read() == b"hello from first inner file"
    assert captured.out == (
        f"Making directory: `{target_dir}`...\n"
        f"Making directory: `{inner_dir}`...\n"
        f"Downloading file: `{file_in_inner_dir}`...\n"
        f"Downloading file: `{inner_file}`...\n")
    shutil.rmtree(target_dir)


def test_download_doesnt_overwrite(tmpdir, wrapper):
    test_file = tmpdir.join("test_file.txt")
    test_file.write("")
    remote_target = Mock()
    remote_target.name = test_file.basename
    test_content = b"check that this content will not disappear"
    test_file.write_binary(test_content)
    with patch("gdrive_wrapper.print_ow_dialog") as ow_mock:
        with pytest.raises(FileExistsError):
            wrapper.download(remote_target, test_file.dirname)
        ow_mock.assert_not_called()
    assert test_file.read_binary() == test_content


def test_download_to_custom_directory(tmpdir, capsys, wrapper):
    remote_target = Mock()
    remote_target.name = "some_name"
    remote_target.type = "file"
    test_dir = tmpdir.mkdir("temp_dir")
    assert os.path.exists(test_dir)
    wrapper._gdrive.download = Mock(return_value=b"hello from testfile")
    wrapper.download(remote_target, test_dir, ov=True)
    wrapper._gdrive.download.assert_called_once_with(remote_target.id)
    download_dest = os.path.join(test_dir, remote_target.name)
    assert os.path.exists(download_dest)
    with open(download_dest, "rb") as f:
        assert f.read() == b"hello from testfile"
    captured = capsys.readouterr()
    assert captured.out == f"Downloading file: `{download_dest}`...\n"


def test_download_overwrite(tmpdir, capsys, wrapper):
    remote_target = Mock()
    remote_target.name = "test.txt"
    remote_target.type = "file"
    test_file = tmpdir.mkdir("test_dir").join("test.txt")
    test_file.write_binary(b"hello from test file")
    with patch("gdrive_wrapper.print_ow_dialog") as ow_mock:
        wrapper._gdrive.download = Mock(
            return_value=b"erased data"
        )
        wrapper.download(remote_target, test_file.dirname, ov=True)
        dowload_dest = os.path.abspath(os.path.join(test_file.dirname, remote_target.name))
        ow_mock.assert_called_once_with(dowload_dest)
        with open(dowload_dest, "rb") as f:
            assert f.read() == b"erased data"
