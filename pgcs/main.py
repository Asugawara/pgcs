import argparse
import os

import gcsfs

from pgcs.custom_select import traverse_gcs
from pgcs.preferences import PREF_FILE_PATH, GCSPref


def main() -> None:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="cmd")
    parser_traverse = subparsers.add_parser(
        "traverse", help="default positional argument `pgcs` == `pgcs traverse`"
    )
    parser_pref = subparsers.add_parser("pref", help="set pref")
    parser_pref.add_argument("--init", action="store_true")
    parser_pref.add_argument("key", nargs="?")
    parser_pref.add_argument("value", nargs="?")
    parser.set_defaults(cmd="traverse")
    args = parser.parse_args()

    pref = GCSPref.parse_file(PREF_FILE_PATH) if PREF_FILE_PATH.exists() else GCSPref()
    if args.cmd == "traverse":
        gfs = gcsfs.GCSFileSystem(os.getenv("PROJECT_ID", pref.default_project_id))
        traverse_gcs(gfs.buckets)
    elif args.cmd == "pref":
        if args.init:
            new_pref = GCSPref()
        elif args.key and args.value:
            new_pref = pref.model_copy(update={args.key: args.value})
        else:
            raise ValueError
        new_pref.write()
    else:
        raise NotImplementedError


if __name__ == "__main__":
    main()
