import pytest
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

# def test_lsdir(wrapper):
