import argparse
import os
import pickle
from typing import Dict

import gcsfs

from pgcs.custom_select import traverse_gcs
from pgcs.file_system.base import Entry
from pgcs.file_system.entries import Bucket
from pgcs.preferences import PREF_FILE_PATH, GCSPref

gfs = gcsfs.GCSFileSystem()


def main() -> None:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="cmd")
    parser_traverse = subparsers.add_parser(
        "traverse", help="default positional argument `pg` == `pg traverse`"
    )
    parser_pref = subparsers.add_parser("pref", help="set pref")
    parser_pref.add_argument("--init", action="store_true")
    parser_pref.add_argument("key", nargs="?")
    parser_pref.add_argument("value", nargs="?")
    parser.set_defaults(cmd="traverse")
    args = parser.parse_args()

    pref = GCSPref.read() if PREF_FILE_PATH.exists() else GCSPref()
    if args.cmd == "traverse":
        root: Dict[str, Entry] = {}
        for bucket in gfs.buckets:
            if os.path.exists(pref.cache_dir / bucket.rstrip("/")):
                with open(pref.cache_dir / bucket.rstrip("/"), "rb") as f:
                    root[bucket] = pickle.load(f)
            else:
                root[bucket] = Bucket(bucket.rstrip("/"), root)
        traverse_gcs(root)
        for bucket in root.values():
            bucket.save(pref.cache_dir, force=True)

    elif args.cmd == "pref":
        if args.init:
            new_pref = GCSPref()
        elif args.key and args.value:
            if args.value in ("True", "False"):
                args.value = bool(args.value)
            new_pref = pref.model_copy(update={args.key: args.value})
        else:
            raise ValueError
        new_pref.write()
    else:
        raise NotImplementedError


if __name__ == "__main__":
    main()
