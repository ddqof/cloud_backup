import sys
from ._remote_storage import RemoteStorage as _RemoteStorage


__all__ = ["RemoteStorage"]

RemoteStorage = _RemoteStorage(sys.argv[1] if len(sys.argv) == 2 else "gdrive")
# TODO: remove sys.argv when deploy
