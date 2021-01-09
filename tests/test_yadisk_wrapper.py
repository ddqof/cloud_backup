import pytest
import os
import shutil
from unittest.mock import Mock, call, patch
from yadisk_wrapper import YaDiskWrapper
from cloudbackup.yadisk import YaDisk


@pytest.fixture()
def wrapper():
    with patch("test_yadisk_wrapper.YaDisk"):
        yield YaDiskWrapper(YaDisk())


def test_upload_dir(tmpdir, wrapper):
    test_dir = tmpdir.mkdir("test_dir")
    first_file = tmpdir.join("first_file.txt")
    first_file.write_binary(b"hello from first file")
    second_file = tmpdir.join("second_file.txt")
    second_file.write_binary(b"hello from second file")
    inner_file = test_dir.join("inner_file.txt")
    inner_file.write(b"hello from inner file")



    wrapper.upload(test_dir)
