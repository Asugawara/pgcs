import json
from pathlib import Path

from pydantic import BaseModel

PREF_FILE_PATH = Path(__file__).parent / ".preference"
PREF_CACHE_DIR = Path(__file__).parent / ".cache"


class GCSPref(BaseModel, frozen=True):
    ignore_case: bool = True
    cache_dir: Path = PREF_CACHE_DIR

    def write(self) -> None:
        PREF_FILE_PATH.write_text(self.model_dump_json())

    @classmethod
    def read(cls) -> "GCSPref":
        with PREF_FILE_PATH.open() as f:
            return cls.model_validate(json.load(f))
