import os
import pickle
from unittest.mock import patch

import pytest

from pgcs.file_system.entries import Bucket, Directory, File


def test_bucket_init():
    root = {}
    bucket = Bucket("test_bucket", root)
    assert bucket.name == "test_bucket"
    assert bucket.root == root
    assert bucket.children == {}


def test_bucket_path():
    root = {}
    bucket = Bucket("test_bucket", root)
    assert bucket.path() == "gs://test_bucket"


def test_bucket_get():
    root = {}
    bucket = Bucket("test_bucket", root)
    entry = bucket.get("test_entry")
    assert entry is None

    new_dir = Directory("test_entry", bucket)
    bucket.add(new_dir)
    assert bucket.get("test_entry") == new_dir


def test_bucket_add():
    root = {}
    bucket = Bucket("test_bucket", root)
    new_dir = Directory("test_entry", bucket)
    bucket.add(new_dir)
    assert bucket.children == {"test_entry": new_dir}

    # Adding entry with path outside the bucket should not add it to the children
    same_name_dir = Directory("test_entry", bucket)
    bucket.add(same_name_dir)
    assert bucket.children == {"test_entry": new_dir}


def test_bucket_ls():
    root = {}
    bucket = Bucket("test_bucket", root)
    entry1 = Directory("test_entry1", bucket)
    entry2 = Directory("test_entry2", bucket)
    bucket.add(entry1)
    bucket.add(entry2)
    assert bucket.ls() == [
        "gs://test_bucket/test_entry1",
        "gs://test_bucket/test_entry2",
    ]


@patch("pgcs.file_system.entries.os")
def test_bucket_save(mock_os):
    root = {}
    bucket = Bucket("test_bucket", root)
    new_dir = Directory("test_entry", bucket)
    bucket.add(new_dir)

    mock_os.path.exists.return_value = False
    mock_os.path.join.return_value = "save_dir/test_bucket"

    with patch("pgcs.file_system.entries.open") as mock_open:
        bucket.save("save_dir", force=True)
        mock_os.makedirs.assert_called_once_with("save_dir", exist_ok=True)
        mock_open.assert_called_once_with("save_dir/test_bucket", "wb")
        mock_open().__enter__().write.assert_called_once_with(pickle.dumps(bucket))

    mock_os.path.exists.return_value = True

    with patch("pgcs.file_system.entries.open") as mock_open:
        bucket.save("save_dir", force=False)
        mock_os.makedirs.assert_called_with("save_dir", exist_ok=True)
        mock_open.assert_not_called()


def test_file_init():
    parent = Bucket("test_bucket", {})
    file = File("test_file", parent)
    assert file.name == "test_file"
    assert file.parent == parent


def test_file_path():
    parent = Bucket("test_bucket", {})
    file = File("test_file", parent)
    assert file.path() == "gs://test_bucket/test_file"


def test_file_add():
    parent = Bucket("test_bucket", {})
    file = File("test_file", parent)
    with pytest.raises(NotImplementedError):
        file.add(Bucket("test_entry", {}))


def test_directory_init():
    parent = Directory("test_parent", None)
    directory = Directory("test_directory", parent)
    assert directory.name == "test_directory"
    assert directory.parent == parent
    assert directory.children == {}


def test_directory_path():
    bucket = Bucket("test_bucket", {})
    parent = Directory("test_parent", bucket)
    directory = Directory("test_directory", parent)
    assert directory.path() == "gs://test_bucket/test_parent/test_directory"


def test_directory_get():
    bucket = Bucket("test_bucket", {})
    parent = Directory("test_parent", bucket)
    directory = Directory("test_directory", parent)
    entry = Directory("test_entry", directory)
    directory.add(entry)
    assert directory.get("test_entry") == entry
    assert directory.get("nonexistent_entry") is None


def test_directory_add():
    bucket = Bucket("test_bucket", {})
    parent = Directory("test_parent", bucket)
    directory = Directory("test_directory", parent)
    entry = Directory("test_entry", directory)
    directory.add(entry)
    assert directory.children == {"test_entry": entry}

    # Adding entry with path outside the directory should not add it to the children
    other_entry = Directory("other_directory/test_entry", parent)
    directory.add(other_entry)
    assert directory.children == {"test_entry": entry}


def test_directory_ls():
    bucket = Bucket("test_bucket", {})
    parent = Directory("test_parent", bucket)
    directory = Directory("test_directory", parent)
    entry1 = Directory("test_entry1", directory)
    entry2 = Directory("test_entry2", directory)
    directory.add(entry1)
    directory.add(entry2)
    assert directory.ls() == [
        "gs://test_bucket/test_parent/test_directory/test_entry1",
        "gs://test_bucket/test_parent/test_directory/test_entry2",
    ]
