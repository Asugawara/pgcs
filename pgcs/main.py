import argparse

import gcsfs

from pgcs.custom_select import traverse_gcs
from pgcs.preferences import PREF_FILE_PATH, GCSPref


def main() -> None:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="cmd")
    parser_traverse = subparsers.add_parser(
        "traverse", help="default positional argument `pg` == `pg traverse`"
    )
    parser_traverse.add_argument("root", nargs="?")
    parser_pref = subparsers.add_parser("pref", help="set pref")
    parser_pref.add_argument("--init", action="store_true")
    parser_pref.add_argument("key", nargs="?")
    parser_pref.add_argument("value", nargs="?")
    parser.set_defaults(cmd="traverse", root=None)
    args = parser.parse_args()

    pref = GCSPref.read() if PREF_FILE_PATH.exists() else GCSPref()
    if args.cmd == "traverse":
        gfs = gcsfs.GCSFileSystem()
        buckets = gfs.ls(args.root) if args.root is not None else gfs.buckets
        traverse_gcs(buckets)
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
