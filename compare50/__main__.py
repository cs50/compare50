import argparse
import contextlib
import os
import pathlib
import tempfile
import termcolor
import textwrap
import shutil
import attr
import sys
import traceback

import attr
import patoolib
import lib50

from . import html_renderer
from . import api, errors, data, comparators


def excepthook(cls, exc, tb):
    if (issubclass(cls, errors.Error) or issubclass(cls, lib50.Error)) and exc.args:
        termcolor.cprint(str(exc), "red", file=sys.stderr)
    elif cls is FileNotFoundError:
        termcolor.cprint("{} not found".format(exc.filename), "red", file=sys.stderr)
    elif not issubclass(cls, Exception) and not isinstance(exc, KeyboardInterrupt):
        # Class is some other BaseException, better just let it go
        return
    else:
        termcolor.cprint("Sorry, something's wrong! Let sysadmins@cs50.harvard.edu know!", "red", file=sys.stderr)

    if excepthook.verbose:
        traceback.print_exception(cls, exc, tb)

    sys.exit(1)


# Assume we should print tracebacks until we get command line arguments
excepthook.verbose = True
# sys.excepthook = excepthook


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
        for cfg in data.Pass._get_all():
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


    def fmt_match(arg):
        id, sm = arg
        return id, sm.sub_a.path.name, sm.sub_b.path.name, sm.score

    if submission_matches:
        rows = list(map(fmt_match, enumerate(submission_matches)))
    else:
        rows = [("-", "-", "-", "-")]
    data = Table(rows=rows, names=("id", "Submission A", "Submission B", "Score"))
    ascii.write(data, format="fixed_width")


def main():
    parser = ArgParser(prog="compare50")
    submission_factory = SubmissionFactory()
    parser.add_argument("submissions",
                        nargs="+",
                        help="Paths to submissions to compare")
    parser.add_argument("-a", "--archive",
                        nargs="+",
                        default=[],
                        help="Paths to archive submissions. Archive submissions are not compared against other archive submissions, only against regular submissions.")
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
                        help="Globbing patterns to include from every submission."
                             " Includes everything (*) by default."
                             " Make sure to quote your patterns to escape any shell globbing!")
    parser.add_argument("-x", "--exclude",
                        callback=submission_factory.exclude,
                        nargs="+",
                        action=IncludeExcludeAction,
                        help="Globbing patterns to exclude from every submission."
                             " Nothing is excluded by default."
                             " Make sure to quote your patterns to escape any shell globbing!")
    parser.add_argument("--hidden",
                        action="store_true",
                        help="also include hidden files and directories.")
    parser.add_argument("--log",
                        action="store_true",
                        help="display more detailed information about comparison process.")
    parser.add_argument("--list",
                        action=ListAction)
    parser.add_argument("-o", "--output",
                        action="store",
                        default="html",
                        type=pathlib.Path,
                        help="location of compare50's output")
    parser.add_argument("-v", "--verbose",
                        action="store_true",
                        help="display the full tracebacks of any errors")
    parser.add_argument("-n",
                        action="store",
                        default=50,
                        metavar="MATCHES",
                        type=int,
                        help="number of matches to output")

    args = parser.parse_args()
    excepthook.verbose = args.verbose

    if len(args.submissions) == 1:
        raise errors.Error("At least two submissions are required for a comparison.")

    # Extract comparator and preprocessors from pass
    try:
        pass_ = data.Pass._get(args.pass_)
    except KeyError:
        raise errors.Error("{} is not a pass, try one of these: {}"\
                            .format(args.pass_, [c.__name__ for c in data.Pass._get_all()]))

    comparator = pass_.comparator
    preprocessor = Preprocessor(pass_.preprocessors)

    # Collect all submissions, archive submissions and distro files
    with lib50.ProgressBar("Preparing"):
        subs = submission_factory.get_all(args.submissions, preprocessor)
        archive_subs = submission_factory.get_all(args.archive, preprocessor)
        ignored_subs = submission_factory.get_all(args.distro, preprocessor)
        ignored_files = [f for sub in ignored_subs for f in sub.files]

    # Cross compare and rank all submissions, keep only top `n`
    with lib50.ProgressBar("Ranking"):
        submission_matches = api.rank_submissions(subs, archive_subs, ignored_files, comparator, n=args.n)

    # Get the matching spans, group them per submission
    with lib50.ProgressBar("Comparing"):
        groups = api.create_groups(submission_matches, comparator, ignored_files)

    # Render results
    with lib50.ProgressBar("Rendering"):
        html_renderer.render(groups, dest=args.output)

    print_results(submission_matches)


PROFILE =[]
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
#
# PROFILE = [ main
          # , api.create_groups
          # , comparators.winnowing.Winnowing.cross_compare
          # , comparators.winnowing.Winnowing.create_spans
          # , comparators.winnowing.Index.hashes
          # , comparators.winnowing.CompareIndex.fingerprint
          # , comparators.winnowing.CrossCompareIndex.fingerprint
          # , comparators.winnowing.Winnowing._create_spans.__call__
          # ]

if __name__ == "__main__":
    if PROFILE:
        outfile = "profile.txt"
        import termcolor
        from line_profiler import LineProfiler
        profiler = LineProfiler()
        for f in PROFILE:
            profiler.add_function(f)
        profiler.enable_by_count()
        try:
            main()
        finally:
            with open(outfile, "w") as f:
                profiler.print_stats(stream=f)
            termcolor.cprint(f"Profiling data written to {outfile}", "yellow")
    else:
        main()
