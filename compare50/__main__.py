import argparse
import contextlib
import os
import pathlib
import tempfile
import textwrap
import shutil
import attr

import attr
import patoolib

from . import html_renderer
from . import passes, api, errors, data, comparators

# Supported archives, per https://github.com/wummel/patool
ARCHIVES = ( [".bz2"]
           , [".tar"]
           , [".tar", ".gz"]
           , [".tgz"]
           , [".zip"]
           , [".7z"]
           , [".xz"] )

@contextlib.contextmanager
def get(generator, paths, preprocessor):
    """
    Calls generator for every path.
    If path is a compressed file, first unpacks it into a temporary dir.
    """
    if not paths:
        yield []
        return

    temp_dirs = []
    content = []

    try:
        for path in paths:
            path = pathlib.Path(path)

            if not is_archive(path):
                content.extend(generator(path, preprocessor))
            else:
                temp_dirs.append(tempfile.mkdtemp())
                temp_path = pathlib.Path(temp_dirs[-1])
                unpack(path, temp_path)
                content.extend(generator(temp_path, preprocessor, archive_path=path))
        yield content
    finally:
        for d in temp_dirs:
            shutil.rmtree(d)


def unpack(path, dest):
    """Unpacks compressed file in path to dest."""
    path = pathlib.Path(path)
    dest = pathlib.Path(dest)

    if not dest.exists():
        raise errors.Error("Unpacking destination: {} does not exist.".format(dest))

    if is_archive(path):
        try:
            patoolib.extract_archive(str(path), outdir=str(dest), verbosity=-1)
            return dest
        except patoolib.util.PatoolError:
            raise errors.Error("Failed to extract: {}".format(path))
    else:
        raise errors.Error("Unsupported archive, try one of these: {}".format(ARCHIVES))


def is_archive(path):
    return path.suffixes in ARCHIVES


def individual_submission(path, preprocessor, archive_path=None):
    path = pathlib.Path(path).absolute()

    if path.is_file():
        if archive_path:
            return (data.Submission.from_file_path(path, preprocessor, submission_name=archive_path),)
        else:
            return (data.Submission.from_file_path(path, preprocessor),)

    name = str(archive_path) if archive_path else str(path)
    return (data.Submission(path, preprocessor, name=name),)


def submissions(path, preprocessor, archive_path=None):
    path = pathlib.Path(path).absolute()
    if path.is_file():
        return individual_submission(path, preprocessor, archive_path=archive_path)

    subs = []
    for root, dirs, files in os.walk(path):
        # Keep walking until you stumble upon a single file or multiple items
        if len(dirs) == 1 and len(files) == 0:
            continue

        root = pathlib.Path(root).absolute()

        # Create a Submission for every dir
        for dir in dirs:
            name = "{} @ {}".format(archive_path, dir) if archive_path else root / dir
            subs.append(data.Submission(root / dir, preprocessor, name=name))

        # Create a single file Submission for every file
        for file in files:
            file_path = root / file
            if archive_path:
                sub_name = "{} @ {}".format(archive_path, file_path.parent.relative_to(path))
                subs.append(data.Submission.from_file_path(file_path, preprocessor, submission_name=sub_name))
            else:
                subs.append(data.Submission.from_file_path(file_path, preprocessor))
        break
    return subs


def files(path, preprocessor, archive_path=None):
    return list(individual_submission(path, preprocessor, archive_path=archive_path).files())


class ListAction(argparse.Action):
    """Hook into argparse to allow a list flag"""
    def __init__(self, option_strings, dest=argparse.SUPPRESS, default=argparse.SUPPRESS, help="List all available passes and exit."):
        super().__init__(option_strings, dest=dest, nargs=0, default=default, help=help)

    def __call__(self, parser, namespace, values, option_string=None):
        indentation = "    "
        for cfg in passes.get_all():
            print(str(cfg.__name__))
            for line in textwrap.wrap(cfg.description, 80 - len(indentation)):
                print("{}{}".format(indentation, line))
        parser.exit()


@attr.s(slots=True)
class Preprocessor:
    """Hack to ensure that composed preprocessor is serializable by Pickle."""
    preprocessors = attr.ib()

    def __call__(self, tokens):
        for preprocessor in self.preprocessors:
            tokens = preprocessor(tokens)
        return tokens


# Temporary function to print results as an ascii table
def print_results(submission_matches):
    from astropy.io import ascii
    from astropy.table import Table


    def fmt_match(sm):
        return (sm.sub_a.path.name, sm.sub_b.path.name, sm.score)

    if submission_matches:
        rows = list(map(fmt_match, submission_matches))
    else:
        rows = [("-", "-", "-")]
    data = Table(rows=rows, names=("Submission A", "Submission B", "Score"))
    ascii.write(data, format="fixed_width")


def main():
    parser = argparse.ArgumentParser(prog="compare50")
    parser.add_argument("submissions",
                        nargs="+",
                        help="Path to directory or compressed file containing submissions. If more than one argument is passed compare50 treats them as individual submissions.")
    parser.add_argument("-a", "--archive",
                        action="append",
                        default=[],
                        help="Path to directory or compressed file containing archive submissions at the top level (can be specified multiple times)")
    parser.add_argument("-d", "--distro",
                        action="append",
                        default=[],
                        help="Paths to directory or compressed file containing distro files to ignore at the top level (can be specified multiple times).")
    parser.add_argument("-p", "--pass",
                        action="store",
                        dest="pass_",
                        help="Specify which pass to use.")
    parser.add_argument("--hidden",
                        action="store_true",
                        help="Also include hidden files and directories.")
    parser.add_argument("--log",
                        action="store_true",
                        help="Display more detailed information about comparison process.")
    parser.add_argument("--list",
                        action=ListAction)

    args = parser.parse_args()

    # Validate args
    for items in (args.submissions, args.archive, args.distro):
        for item in items:
            if not pathlib.Path(item).exists():
                raise errors.Error("Path {} does not exist.".format(item))


    # Extract comparator and preprocessors from pass
    try:
        pass_ = passes.get(args.pass_)
    except KeyError:
        raise errors.Error("{} is not a pass, try one of these: {}"\
                            .format(args.pass_, [c.__name__ for c in passes.get_all()]))

    comparator = pass_.comparator
    preprocessor = Preprocessor(pass_.preprocessors)

    sub_gen = submissions if len(args.submissions) == 1 else individual_submission

    # Collect all submissions, archive submissions and distro files
    with get(sub_gen, args.submissions, preprocessor) as subs,\
         get(submissions, args.archive, preprocessor) as archive_subs,\
         get(files, args.distro, preprocessor) as ignored_files:

        # Cross compare and rank all submissions, keep only top `n`
        submission_matches = api.rank_submissions(subs, archive_subs, ignored_files, comparator, n=50)

        print_results(submission_matches)

        # Get the matching spans, group them per submission
        groups = api.create_groups(submission_matches, comparator, ignored_files)

        html_renderer.render(groups)
        # TODO api.as_json(groups)

# PROFILE = [ main
#           , api.rank_submissions
#           , comparators.misspellings.Misspellings.cross_compare
#           , comparators.misspellings.Misspellings.create_spans
#           , api.create_groups]

PROFILE = []
if __name__ == "__main__":
    if PROFILE:
        from line_profiler import LineProfiler
        profiler = LineProfiler()
        for f in PROFILE:
            profiler.add_function(f)
        profiler.enable_by_count()
        try:
            main()
        finally:
            profiler.print_stats()
    else:
        main()
