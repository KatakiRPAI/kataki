"""Kataki RPAI engine: headless AI roleplay harness."""

import os
from pathlib import Path

__version__ = "0.0.1"


def data_dir() -> Path:
    """Where Kataki keeps its library and downloaded models. KATAKI_HOME overrides it."""
    if home := os.environ.get("KATAKI_HOME"):
        return Path(home)
    base = os.environ.get("APPDATA") or os.environ.get("XDG_DATA_HOME")
    return Path(base or Path.home() / ".local/share") / "Kataki"
