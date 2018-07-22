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
from tempfile import TemporaryDirectory as temp_dir


def get_submissions(path, preprocessors):
    result = []
    for item in os.listdir(path):
        item = pathlib.Path(item)
        if item.is_dir():
            result.append(data.Submission(item))
    return result


def get_files(path, preprocessors):
    return list(data.Submission(path, preprocessors).files())


def unpack(path, dest):
    # Supported archives, per https://github.com/wummel/patool
    path = pathlib.Path(path)

    ARCHIVES = (".bz2", ".tar", ".tar.gz", ".tgz", ".zip", ".7z", ".xz")

    if str(path).lower().endswith(ARCHIVES):
        try:
            patoolib.extract_archive(pathname, outdir=dest)
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

    with temp_dir() as sub_dir, temp_dir() as archive_dir, temp_dir() as distro_dir:
        if pathlib.Path(args.submissions).is_dir():
            submissions = get_submissions(args.submissions, preprocessors)
        else:
            submissions = get_submissions(unpack(args.submissions, sub_dir), preprocessors)

        if args.archive:
            if pathlib.Path(args.archive).is_dir():
                submissions = get_submissions(args.archive, preprocessors)
            else:
                submissions = get_submissions(unpack(args.archive, sub_dir), preprocessors)

        if args.distro:
            if pathlib.Path(args.distro).is_dir():
                submissions = get_files(args.distro, preprocessors)
            else:
                submissions = get_files(unpack(args.distro, sub_dir), preprocessors)

    #submissions = unpack(args.submissions)
    #archive_submissions = unpack(args.archive)
    #distr_files = unpack(args.distro)

    # TODO cross_compare, group by sub, rank, filter top n
    submissions = [Submission("tests/files/sub_a"), Submission("tests/files/sub_b"), Submission("tests/files/sub_c")]
    archive_submissions = []
    ignored_files = []
    submission_matches = api.rank_submissions(submissions, archive_submissions, ignored_files, comparator, n=50)
    for sm in submission_matches:
        print(sm.sub_a)
        print(sm.sub_b)
    # TODO create spans, group spans per sub_match
    # groups = api.create_groups(submission_matches, comparator)

    # TODO
    # html = api.render(groups)
