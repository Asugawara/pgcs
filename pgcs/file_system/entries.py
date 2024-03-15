from __future__ import annotations

import os
import pickle
from typing import Dict, List, Optional, Tuple

import gcsfs

from pgcs.file_system.base import Entry

gfs = gcsfs.GCSFileSystem()


class File(Entry):
    def __init__(self, name: str, parent: Entry) -> None:
        super().__init__(name)
        self._parent = parent
        self._created_at: str = ""
        self._updated_at: str = ""

    @property
    def parent(self) -> Entry:
        return self._parent

    def path(self) -> str:
        return "/".join((self._parent.path(), self._name))

    def add(self, entry: Entry) -> None:
        raise NotImplementedError

    def stat(self) -> Tuple[str, str]:
        if self._created_at and self._updated_at:
            return (self._created_at, self._updated_at)
        file_stats = gfs.stat(self.path())
        self._created_at = file_stats.get("timeCreated", "")
        self._updated_at = file_stats.get("updated", "")
        return (self._created_at, self._updated_at)


class Directory(Entry):
    def __init__(self, name: str, parent: Entry) -> None:
        super().__init__(name)
        self._parent = parent
        self._children: Dict[str, Entry] = {}

    @property
    def parent(self) -> Entry:
        return self._parent

    @property
    def children(self) -> Dict[str, Entry]:
        return self._children

    def path(self) -> str:
        return "/".join((self._parent.path(), self._name))

    def get(self, entry_name: str, default: Optional[Entry] = None) -> Optional[Entry]:
        return self._children.get(entry_name, default)

    def add(self, entry: Entry) -> None:
        if entry.name and entry.path().startswith(self.path()):
            if entry.name not in self._children:
                self._children[entry.name] = entry

    def load(self, force: bool = False) -> None:
        if force:
            self._children = {}
        if not self._children:
            for _, dirnames, filenames in gfs.walk(self.path(), maxdepth=1):
                print(f"{dirnames=}, {filenames=}")
                for dirname in dirnames:
                    self.add(Directory(dirname, self))
                for filename in filenames:
                    self.add(File(filename, self))

    def ls(self) -> List[str]:
        return [entry.path() for entry in self._children.values()]


class Bucket(Entry):
    def __init__(self, name: str, root: Dict[str, Entry]) -> None:
        super().__init__(name)
        self._root = root
        self._children: Dict[str, Entry] = {}

    @property
    def root(self) -> Dict[str, Entry]:
        return self._root

    @property
    def children(self) -> Dict[str, Entry]:
        return self._children

    def path(self) -> str:
        return f"gs://{self._name}"

    def get(self, entry_name: str, default: Optional[Entry] = None) -> Optional[Entry]:
        return self._children.get(entry_name, default)

    def add(self, entry: Entry) -> None:
        if entry.name and entry.path().startswith(self.path()):
            if entry.name not in self._children:
                self._children[entry.name] = entry

    def load(self, force: bool = False) -> None:
        if force:
            self._children = {}
        if not self._children:
            for _, dirnames, filenames in gfs.walk(self.path(), maxdepth=1):
                for dirname in dirnames:
                    if dirname:
                        self.add(Directory(dirname, self))
                for filename in filenames:
                    if filename:
                        self.add(File(filename, self))

    def ls(self) -> List[str]:
        return [entry.path() for entry in self._children.values()]

    def save(self, save_dir: str, force: bool = False) -> None:
        os.makedirs(save_dir, exist_ok=True)
        file_path = os.path.join(save_dir, self.name)
        if force or not os.path.exists(file_path):
            with open(file_path, "wb") as f:
                pickle.dump(self, f)
