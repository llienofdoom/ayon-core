from __future__ import annotations
from typing import Optional, TypedDict


class HostContextData(TypedDict):
    project_name: str
    folder_path: Optional[str]
    task_name: Optional[str]
