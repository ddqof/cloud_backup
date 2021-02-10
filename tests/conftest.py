import pytest
import shutil
from pathlib import Path
from collections import namedtuple


@pytest.fixture()
def not_existing_file():
    p = Path("testfile.txt")
    if p.exists():
        raise FileExistsError
    yield p
    p.unlink()


@pytest.fixture()
def not_existing_dir():
    p = Path("test_dir")
    if p.exists():
        raise FileExistsError
    yield p
    shutil.rmtree(p)


@pytest.fixture()
def complex_dir(tmp_path):
    """
    tmp_path/
    |-- dir_1
    |   |-- file_1.txt
    |   `-- file_2.txt
    |-- dir_2
    |   `-- file_3.txt
    `-- file_4.txt
    """
    dir_1 = tmp_path / "dir_1"
    file_1 = dir_1 / "file_1.txt"
    file_2 = dir_1 / "file_2.txt"
    dir_2 = tmp_path / "dir_2"
    file_3 = dir_2 / "file_3.txt"
    file_4 = tmp_path / "file_4.txt"
    dir_1.mkdir()
    dir_2.mkdir()
    file_1.touch()
    file_2.touch()
    file_3.touch()
    file_4.touch()
    ComplexDir = namedtuple(
        "ComplexDir",
        ["path", "dir_1", "dir_2", "file_1", "file_2", "file_3", "file_4"]
    )
    return ComplexDir(
        tmp_path, dir_1, dir_2, file_1, file_2, file_3, file_4
    )
