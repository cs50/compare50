import argparse
import textwrap
from . import config
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
def submissions(path, preprocessors):
    if not path:
        yield []
        return

    path = pathlib.Path(path)
    if not path.is_dir():
        with TemporaryDirectory() as dir:
            yield _submissions_from_dir(unpack(path, dir), preprocessors)
    else:
        yield _submissions_from_dir(path, preprocessors)


@contextlib.contextmanager
def files(path, preprocessors):
    if not path:
        yield []
        return

    path = pathlib.Path(path)
    if not path.is_dir():
        with TemporaryDirectory() as dir:
            yield _files_from_dir(unpack(path, dir), preprocessors)
    else:
        yield _files_from_dir(path, preprocessors)


def _submissions_from_dir(dir, preprocessors):
    path = pathlib.Path(dir).absolute()
    result = []
    for item in os.listdir(path):
        item = path / item
        if item.is_dir():
            result.append(data.Submission(item))
    return result


def _files_from_dir(path, preprocessors):
    return list(data.Submission(path, preprocessors).files())


def unpack(path, dest):
    # Supported archives, per https://github.com/wummel/patool
    path = pathlib.Path(path)

    ARCHIVES = (".bz2", ".tar", ".tar.gz", ".tgz", ".zip", ".7z", ".xz")

    if str(path).lower().endswith(ARCHIVES):
        try:
            patoolib.extract_archive(path, outdir=dest)
            return dest
        except patoolib.util.PatoolError:
            raise errors.Error(f"Failed to extract: {path}")
    else:
        raise errors.Error(f"Unsupported archive, try one of these: {ARCHIVES}")


class ListAction(argparse.Action):
    """Hook into argparse to allow a list flag"""

    def __init__(self, option_strings, dest=argparse.SUPPRESS, default=argparse.SUPPRESS, help="List all available comparators and exit."):
        super().__init__(option_strings, dest=dest, nargs=0, default=default, help=help)

    def __call__(self, parser, namespace, values, option_string=None):
        indentation = "    "
        for cfg in config.all():
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

    try:
        c = config.get(args.comparator) if args.comparator else config.get()
    except KeyError:
        raise errors.Error(f"{args.comparator} is not a comparator, try one of these: {[c.id() for c in config.all()]}")

    comparator = c.comparator()
    preprocessors = c.preprocessors()

    # Validate args.submissions exists
    if not pathlib.Path(args.submissions).exists():
        raise errors.Error("Path {args.submissions} does not exist.")

    # Validate args.archive and args.distro exist if specified
    for optional_item in [args.archive, args.distro]:
        if optional_item and not pathlib.Path(optional_item).exists():
            raise errors.Error("Path {optional_item} does not exist.")

    with submissions(args.submissions, preprocessors) as subs,\
         submissions(args.archive, preprocessors) as archive_subs,\
         files(args.distro, preprocessors) as ignored_files:

        submission_matches = api.rank_submissions(subs, archive_subs, ignored_files, comparator, n=50)
        for sm in submission_matches:
            print(sm.sub_a)
            print(sm.sub_b)

        # TODO create spans, group spans per sub_match
        # groups = api.create_groups(submission_matches, comparator)

        # TODO
        # html = api.render(groups)
