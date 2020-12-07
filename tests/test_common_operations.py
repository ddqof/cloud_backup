import pytest
from unittest.mock import patch, Mock
from cloudbackup.gdrive import GDrive
from cloudbackup.yadisk import YaDisk
from common_operations import (put_file,
                               remove_remote_file,
                               print_ow_dialog,
                               print_remote_file)


@pytest.fixture()
def test_file(tmpdir):
    test_file = tmpdir.join("test_file.txt")
    test_file.write("")
    return test_file


@pytest.fixture()
def test_dir(tmpdir):
    return tmpdir.mkdir("tmp_dir")


def test_overwrite_dialog_with_existing_file(test_file, capsys):
    with patch("builtins.input") as input_mock:
        input_mock.return_value = "y"
        print_ow_dialog(test_file)
        input_mock.assert_called_once_with(f"Are you sure you want to"
                                           f" overwrite file: `{test_file}`?"
                                           f" ([y]/n) ")
    captured = capsys.readouterr()
    assert captured.out == f"Overwriting file: `{test_file}`...\n"


def test_overwrite_dialog_with_existing_dir(test_dir, capsys):
    with patch("builtins.input") as input_mock:
        input_mock.return_value = "y"
        print_ow_dialog(test_dir)
        input_mock.assert_called_once_with(f"Are you sure you want to"
                                           f" overwrite directory: "
                                           f"`{test_dir}`? ([y]/n) ")
    captured = capsys.readouterr()
    assert captured.out == f"Overwriting directory: `{test_dir}`...\n"


def test_overwrite_dialog_invalid_value(capsys):
    with pytest.raises(ValueError) as e:
        print_ow_dialog("any_invalid_path")
    assert str(e.value) == ("`path` has unexpected value:"
                            " any_invalid_path")
    captured = capsys.readouterr()
    assert captured.out == ""


def test_overwrite_deny(test_dir, capsys):
    with patch("builtins.input") as input_mock:
        input_mock.return_value = "n"
        with pytest.raises(PermissionError) as e:
            print_ow_dialog(test_dir)
        input_mock.assert_called_once_with(
            f"Are you sure you want to overwrite"
            f" directory: `{test_dir}`? ([y]/n) "
        )
    assert str(e.value) == "No access was granted to overwrite"


@pytest.mark.parametrize(
    "mock_storage",
    [Mock(spec=GDrive), Mock(spec=YaDisk)]
)
def test_remove_dir_permanently(mock_storage, capsys):
    with patch("builtins.input") as input_mock:
        input_mock.return_value = "y"
        testdir = "test_dirname"
        remove_remote_file(
            storage=mock_storage,
            file_name=testdir,
            destination="/",
            file_type="dir",
            permanently=True
        )
        input_mock.assert_called_once_with(f"Are you sure you want to"
                                           f" delete directory:"
                                           f" `{testdir}`? ([y]/n) ")
    captured = capsys.readouterr()
    assert captured.out == f"Successfully deleted directory: `{testdir}`\n"


@pytest.mark.parametrize(
    "mock_storage",
    [Mock(spec=GDrive), Mock(spec=YaDisk)]
)
def test_move_dir_to_trash(mock_storage, capsys):
    with patch("builtins.input") as input_mock:
        input_mock.return_value = "y"
        testdir = "test_dirname"
        remove_remote_file(
            storage=mock_storage,
            file_name=testdir,
            destination="/",
            file_type="dir"
        )
        input_mock.assert_called_once_with(f"Are you sure you want to move"
                                           f" directory: `{testdir}` to"
                                           f" the trash? ([y]/n) ")
    captured = capsys.readouterr()
    assert captured.out == (f"Successfully moved directory:"
                            f" `{testdir}` to the trash\n")


@pytest.mark.parametrize(
    "mock_storage",
    [Mock(spec=GDrive), Mock(spec=YaDisk)]
)
def test_remove_file_permanently(mock_storage, capsys):
    with patch("builtins.input") as input_mock:
        input_mock.return_value = "y"
        testfile = "test_filename"
        remove_remote_file(
            storage=mock_storage,
            file_name=testfile,
            destination="/",
            file_type="file",
            permanently=True
        )
        input_mock.assert_called_once_with(f"Are you sure you want to delete"
                                           f" file: `{testfile}`? ([y]/n) ")
    captured = capsys.readouterr()
    assert captured.out == f"Successfully deleted file: `{testfile}`\n"


@pytest.mark.parametrize(
    "mock_storage",
    [Mock(spec=GDrive), Mock(spec=YaDisk)]
)
def test_move_file_to_trash(mock_storage, capsys):
    with patch("builtins.input") as input_mock:
        input_mock.return_value = "y"
        testfile = "test_filename"
        remove_remote_file(
            storage=mock_storage,
            file_name=testfile,
            destination="/",
            file_type="file"
        )
        input_mock.assert_called_once_with(f"Are you sure you want to"
                                           f" move file: `{testfile}`"
                                           f" to the trash? ([y]/n) ")
    captured = capsys.readouterr()
    assert captured.out == (f"Successfully moved file:"
                            f" `{testfile}` to the trash\n")


@pytest.mark.parametrize(
    "mock_storage",
    [Mock(spec=GDrive), Mock(spec=YaDisk)]
)
def test_deny_remove(mock_storage, capsys):
    with patch("builtins.input") as input_mock:
        input_mock.return_value = "n"
        testfile = "test_filename"
        with pytest.raises(PermissionError) as e:
            remove_remote_file(
                storage=mock_storage,
                file_name=testfile,
                destination="/",
                file_type="file"
            )
        input_mock.assert_called_once_with(f"Are you sure you want to"
                                           f" move file: `{testfile}`"
                                           f" to the trash? ([y]/n) ")
    assert str(e.value) == "No access was granted to remove"


def test_remove_on_invalid_storage(test_file, capsys):
    mock_storage = Mock()
    with pytest.raises(ValueError) as e:
        remove_remote_file(
            storage=mock_storage,
            file_name=test_file,
            destination="any_dest",
            file_type="file"
        )
    assert str(e.value) == f"`storage` has unexpected value: {mock_storage}"
    mock_storage.remove.assert_not_called()


def test_put_file_gdrive(test_file):
    mock_gdrive = Mock(spec=GDrive)
    mock_gdrive.get_upload_link = Mock(return_value="test_upload_link")
    put_file(
        storage=mock_gdrive,
        local_path=test_file,
        destination="root"
    )
    mock_gdrive.get_upload_link.assert_called_once_with(
        test_file, "root"
    )
    mock_gdrive.upload_file.assert_called_once_with(
        "test_upload_link", test_file.read_binary()
    )


def test_put_file_yadisk(test_file):
    mock_yadisk = Mock(spec=YaDisk)
    mock_yadisk.get_upload_link = Mock(return_value="test_upload_link")
    put_file(
        storage=mock_yadisk,
        local_path=test_file,
        destination=f"/{test_file}"
    )
    mock_yadisk.get_upload_link.assert_called_once_with(f"/{test_file}")
    mock_yadisk.upload_file.assert_called_once_with(
        "test_upload_link", test_file.read_binary()
    )


def test_put_file_invalid_storage(test_file, capsys):
    mock_storage = Mock()
    with pytest.raises(ValueError) as e:
        put_file(
            storage=mock_storage,
            local_path=test_file,
            destination="any_destination"
        )
    assert str(e.value) == f"`storage` has unexpected value: {mock_storage}"
    captured = capsys.readouterr()
    assert captured.out == ""
    mock_storage.upload_file.assert_not_called()


def test_print_remote_file(test_file, capsys):
    print_remote_file(test_file, "some_id", "file")
    captured = capsys.readouterr()
    assert captured.out == f"{test_file} (some_id)\n"


def test_print_remote_dir(test_dir, capsys):
    print_remote_file(test_dir, "some_id", "dir")
    captured = capsys.readouterr()
    assert f"{test_dir} (some_id)" in captured.out
