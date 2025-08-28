import os
from pathlib import PosixPath
from typing import Optional


def get_tool_home_directory() -> PosixPath:
    tool_data_dir = os.environ.get("TOOL_DATA_DIR")
    if not tool_data_dir:
        raise RuntimeError(f"No TOOL_DATA_DIR")

    return PosixPath(tool_data_dir)


# persistent-data
def get_persistent_data_directory(sub_directory: Optional[str] = None):
    home_dir = get_tool_home_directory()
    path = home_dir / "persistent-data"
    if sub_directory:
        path = path / sub_directory
    path.mkdir(parents=True, exist_ok=True)
    return path.absolute()
