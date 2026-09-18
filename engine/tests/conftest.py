import pytest

from kataki import db


@pytest.fixture
def conn(tmp_path):
    c = db.connect(tmp_path / "library.db")
    yield c
    c.close()
