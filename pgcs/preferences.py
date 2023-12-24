from pathlib import Path
from typing import Optional

from pydantic import BaseModel

PREF_FILE_PATH = Path(__file__).parent / ".preference"


class GCSPref(BaseModel, frozen=True):
    default_project_id: Optional[str] = None
    ignore_case: bool = True

    def write(self) -> None:
        PREF_FILE_PATH.write_text(self.json())
