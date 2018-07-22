import argparse
import textwrap
from . import passes
from . import api
from . import errors
from . import data
from .data import Submission
import patoolib
import pathlib
import os
import contextlib
from tempfile import TemporaryDirectory

@contextlib.contextmanager
def submissions(path, preprocessor):
    """
    Creates a data.Submission instance for every top level dir in path.
    If path is a compressed file, first unpacks it into a temporary dir.
    """
    if not path:
        yield []
        return

    path = pathlib.Path(path)
    if not path.is_dir():
        with TemporaryDirectory() as dir:
            yield _submissions_from_dir(unpack(path, dir), preprocessor)
    else:
        yield _submissions_from_dir(path, preprocessor)


@contextlib.contextmanager
def files(path, preprocessor):
    """
    Creates a data.File instance for every file in path.
    If path is a compressed file, first unpacks it into a temporary dir.
    """
    if not path:
        yield []
        return

    path = pathlib.Path(path)
    if not path.is_dir():
        with TemporaryDirectory() as dir:
            yield _files_from_dir(unpack(path, dir), preprocessor)
    else:
        yield _files_from_dir(path, preprocessor)


def unpack(path, dest):
    """Unpacks compressed file in path to dest."""
    # Supported archives, per https://github.com/wummel/patool
    path = pathlib.Path(path)
    dest = pathlib.Path(dest)

    if not dest.exists():
        raise errors.Error(f"Unpacking destination: {dest} does not exist.")

    ARCHIVES = (".bz2", ".tar", ".tar.gz", ".tgz", ".zip", ".7z", ".xz")

    if str(path).lower().endswith(ARCHIVES):
        try:
            patoolib.extract_archive(path, outdir=dest, verbosity=-1)
            return dest
        except patoolib.util.PatoolError:
            raise errors.Error(f"Failed to extract: {path}")
    else:
        raise errors.Error(f"Unsupported archive, try one of these: {ARCHIVES}")


def _submissions_from_dir(dir, preprocessor):
    path = pathlib.Path(dir).absolute()
    result = []
    for item in os.listdir(path):
        item = path / item
        if item.is_dir():
            result.append(data.Submission(item, preprocessor))
    return result


def _files_from_dir(path, preprocessor):
    return list(data.Submission(path, preprocessor).files())


class ListAction(argparse.Action):
    """Hook into argparse to allow a list flag"""

    def __init__(self, option_strings, dest=argparse.SUPPRESS, default=argparse.SUPPRESS, help="List all available comparators and exit."):
        super().__init__(option_strings, dest=dest, nargs=0, default=default, help=help)

    def __call__(self, parser, namespace, values, option_string=None):
        indentation = "    "
        for cfg in passes.get_all():
            print(f"{cfg.id()}")
            for line in textwrap.wrap(cfg.description(), 80 - len(indentation)):
                print(f"{indentation}{line}")
        parser.exit()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(prog="compare50")

    parser.add_argument("submissions", help="Path to directory or .zip file containing submissions at the top level.")
    parser.add_argument("-a", "--archive",
                        action="store",
                        help="Path to directory or .zip file containing archive submissions at the top level.")
    parser.add_argument("-d", "--distro",
                        action="store",
                        help="Path to directory or .zip file containing distro files to ignore at the top level.")
    parser.add_argument("-c", "--comparator",
                        action="store",
                        help="Name of comparator to use")
    parser.add_argument("--log",
                        action="store_true",
                        help="Display more detailed information about comparison process.")
    parser.add_argument("--list",
                        action=ListAction)

    args = parser.parse_args()

    # Validate args.submissions exists
    if not pathlib.Path(args.submissions).exists():
        raise errors.Error("Path {args.submissions} does not exist.")

    # Validate args.archive and args.distro exist if specified
    for optional_item in [args.archive, args.distro]:
        if optional_item and not pathlib.Path(optional_item).exists():
            raise errors.Error("Path {optional_item} does not exist.")

    # Extract comparator and preprocessors from pass
    try:
        pass_ = passes.get(args.comparator)()
    except KeyError:
        raise errors.Error(f"{args.comparator} is not a comparator, try one of these: {[c.__name__ for c in passes.get_all()]}")

    comparator = pass_.comparator
    preprocessors = pass_.preprocessors
    def preprocessor(tokens):
        for pp in preprocessors:
            tokens = pp(tokens)
        return tokens

    # Collect all submissions, archive submissions and distro files
    with submissions(args.submissions, preprocessor) as subs,\
         submissions(args.archive, preprocessor) as archive_subs,\
         files(args.distro, preprocessor) as ignored_files:

        # Cross compare and rank all submissions, keep only top `n`
        submission_matches = api.rank_submissions(subs, archive_subs, ignored_files, comparator, n=50)

        for sm in submission_matches:
            print(sm.sub_a)
            print(sm.sub_b)

        groups = api.create_groups(submission_matches, comparator, ignored_files)
        #print(groups)

        # TODO
        # html = api.render(groups)
