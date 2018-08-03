import argparse
import contextlib
import os
import pathlib
import tempfile
import textwrap
import shutil
import attr
import sys

import attr
import patoolib

import lib50

from . import html_renderer
from . import passes, api, errors, data, comparators

class SubmissionFactory:
    def __init__(self):
        self.patterns = []
        self.submissions = {}

    def include(self, pattern):
        fp = lib50.config.FilePattern(lib50.config.PatternType.Included, pattern)
        self.patterns.append(fp)

    def exclude(self, pattern):
        fp = lib50.config.FilePattern(lib50.config.PatternType.Excluded, pattern)
        self.patterns.append(fp)

    def _get(self, path, preprocessor):
        path = pathlib.Path(path)

        if path.is_file():
            included, excluded = [path.name], []
            path = path.parent
        else:
            included, excluded = lib50.files(self.patterns, root=path, always_exclude=[])

        decodable_files = []
        for file_path in included:
            try:
                with open(path / file_path) as f:
                    f.read()
            except UnicodeDecodeError:
                pass
            else:
                decodable_files.append(file_path)

        if not decodable_files:
            raise errors.Error("Empty submission.")

        return data.Submission(path, decodable_files, preprocessor=preprocessor)

    def get_all(self, paths, preprocessor):
        subs = []
        for sub_path in paths:
            try:
                subs.append(self._get(sub_path, preprocessor))
            except errors.Error:
                pass
        return subs

class ArgParser(argparse.ArgumentParser):
    def error(self, message):
        self.print_help()
        sys.stderr.write('error: %s\n' % message)
        sys.exit(2)

class ListAction(argparse.Action):
    """Hook into argparse to allow a list flag."""
    def __init__(self, option_strings, dest=argparse.SUPPRESS, default=argparse.SUPPRESS, help="List all available passes and exit."):
        super().__init__(option_strings, dest=dest, nargs=0, default=default, help=help)

    def __call__(self, parser, namespace, values, option_string=None):
        indentation = "    "
        for cfg in passes.get_all():
            print(str(cfg.__name__))
            for line in textwrap.wrap(cfg.description, 80 - len(indentation)):
                print("{}{}".format(indentation, line))
        parser.exit()


class IncludeExcludeAction(argparse.Action):
    """Hook into argparse to allow ordering of include/exclude."""
    def __init__(self, option_strings, callback=None, **kwargs):
        super().__init__(option_strings, **kwargs)
        if not callback:
            raise errors.Error("IncludeExcludeAction requires a callback.")
        self.callback = callback

    def __call__(self, parser, namespace, values, option_string=None):
        for v in values:
            self.callback(v)

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
    parser = ArgParser(prog="compare50")
    submission_factory = SubmissionFactory()
    parser.add_argument("submissions",
                        nargs="+",
                        help="Paths to submissions.")
    parser.add_argument("-a", "--archive",
                        nargs="+",
                        default=[],
                        help="Paths to archive submissions. Compare50 does not compare archive submissions versus archive submissions.")
    parser.add_argument("-d", "--distro",
                        nargs="+",
                        default=[],
                        help="Paths to distribution files. Contents of these files are stripped from submissions.")
    parser.add_argument("-p", "--pass",
                        action="store",
                        dest="pass_",
                        metavar="PASS",
                        help="Specify which pass to use.")
    parser.add_argument("-i", "--include",
                        callback=submission_factory.include,
                        nargs="+",
                        action=IncludeExcludeAction,
                        help="Globbing patterns to include from every submission."\
                             " Includes everything (*) by default."\
                             " Make sure to quote your patterns to escape any shell globbing!")
    parser.add_argument("-x", "--exclude",
                        callback=submission_factory.exclude,
                        nargs="+",
                        action=IncludeExcludeAction,
                        help="Globbing patterns to exclude from every submission."\
                             " Nothing is excluded by default."\
                             " Make sure to quote your patterns to escape any shell globbing!")
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

    # Collect all submissions, archive submissions and distro files
    subs = submission_factory.get_all(args.submissions, preprocessor)
    archive_subs = submission_factory.get_all(args.archive, preprocessor)
    ignored_subs = submission_factory.get_all(args.distro, preprocessor)
    ignored_files = [f for sub in ignored_subs for f in sub.files]

    # Cross compare and rank all submissions, keep only top `n`
    submission_matches = api.rank_submissions(subs, archive_subs, ignored_files, comparator, n=50)

    print_results(submission_matches)

    # Get the matching spans, group them per submission
    groups = api.create_groups(submission_matches, comparator, ignored_files)

    html_renderer.render(groups)
    # # TODO api.as_json(groups)
    #


def filter(files):
    kept_files = []

    for file in files:
        with open(file.path, "r") as f:
            try:
                f.read()
                kept_files.append(file)
            except TypeError:
                pass

# PROFILE = [ main
#           , api.rank_submissions
#           , comparators.misspellings.Misspellings.cross_compare
#           , comparators.misspellings.Misspellings.create_spans
#           , api.create_groups]

# PROFILE = [ main
#           , comparators.winnowing.Winnowing.cross_compare
#           , comparators.winnowing.Winnowing.create_spans
#           , comparators.winnowing.Winnowing._create_spans.__call__
#           , data.File.tokens
#           , comparators.winnowing.Index.create_spans
#           , data.SpanMatches.expand]

# PROFILE = [ main
#           , api.create_groups
#           , api.transitive_closure]

# PROFILE = [ main
#           , read_all]

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
