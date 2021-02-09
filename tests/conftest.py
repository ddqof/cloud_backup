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
    file_1 = tmp_path / "file_1.txt"
    file_2 = tmp_path / "file_2.txt"
    file_1.touch()
    file_2.touch()
    inner_dir = tmp_path / "dir"
    inner_dir.mkdir()
    inner_file_1 = inner_dir / "inner_file_1.txt"
    inner_file_2 = inner_dir / "inner_file_2.txt"
    inner_file_1.touch()
    inner_file_2.touch()
    ComplexDir = namedtuple(
        "ComplexDir",
        ["path", "file_1", "file_2", "inner_dir",
         "inner_file_1", "inner_file_2"]
    )
    return ComplexDir(tmp_path, file_1, file_2,
                      inner_dir, inner_file_1, inner_file_2)
