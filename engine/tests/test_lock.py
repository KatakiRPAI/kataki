import pytest

from kataki import lock


def test_a_second_engine_cannot_hold_the_same_library(tmp_path):
    first = lock.hold(tmp_path)
    with pytest.raises(lock.InUse):
        lock.hold(tmp_path)
    first.close()  # the lock goes with the handle (and so with the process)
    lock.hold(tmp_path).close()
