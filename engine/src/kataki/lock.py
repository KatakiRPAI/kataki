"""One engine per library folder: an OS lock on `library.lock`, gone when the process is."""

import os
from pathlib import Path
from typing import IO


class InUse(Exception):
    pass


def hold(folder: Path) -> IO:
    """Lock the library in `folder` until the returned file is closed. Raises `InUse`."""
    f = open(folder / "library.lock", "a+")  # noqa: SIM115 (held open on purpose)
    try:
        f.seek(0)
        if os.name == "nt":
            import msvcrt

            msvcrt.locking(f.fileno(), msvcrt.LK_NBLCK, 1)
        else:
            import fcntl

            fcntl.flock(f, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError:
        f.close()
        raise InUse(f"The library in {folder} is open in another Kataki.") from None
    return f
