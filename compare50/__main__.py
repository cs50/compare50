import argparse
import contextlib
import os
import pathlib
import tempfile
import textwrap
import shutil
import attr
import sys
import traceback
import time

import attr
import patoolib
import lib50
import termcolor

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
sys.excepthook = excepthook


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
        """
        For every path, and every preprocessor, generate a Submission containing that path/preprocessor.
        Returns a list of lists of Submissions.
        """
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
        indentation = " " * 4
        for pass_ in data.Pass._get_all():
            print(str(pass_.__name__))
            for line in textwrap.wrap(pass_.__doc__ or "No description provided", 80 - len(indentation)):
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


#TODO: remove this before we ship
PROFILE = [ api.compare
          , comparators.winnowing.Winnowing.score
          , comparators.winnowing.Winnowing.compare
          , comparators.winnowing.Index.hashes
          , comparators.winnowing.CompareIndex.fingerprint
          , comparators.winnowing.CrossCompareIndex.fingerprint
          , comparators.winnowing.Winnowing._compare.__call__
          ]

@contextlib.contextmanager
def profile():
    import termcolor, time
    from line_profiler import LineProfiler

    epoch = int(time.time())
    outfile = f"compare50_profile_{epoch}.txt"
    profiler = LineProfiler()
    for f in PROFILE:
        profiler.add_function(f)
    profiler.enable_by_count()
    try:
        yield
    finally:
        with open(outfile, "w") as f:
            profiler.print_stats(stream=f)
        termcolor.cprint(f"Profiling data written to {outfile}", "yellow")


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
    parser.add_argument("-p", "--passes",
                        dest="passes",
                        nargs="+",
                        metavar="PASSES",
                        default=["StripAll"],
                        help="Specify which passes to use. compare50 ranks only by the first pass, but will render views for every pass.")
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

    # TODO: remove these before we ship
    parser.add_argument("--profile",
                        action="store_true",
                        help="profile compare50 (development only, implies debug)")

    parser.add_argument("--debug",
                        action="store_true",
                        help="don't run anything in parallel, disable progress bar")

    args = parser.parse_args()

    excepthook.verbose = args.verbose
    # TODO: remove this before we ship
    excepthook.verbose = True

    if len(args.submissions) == 1:
        raise errors.Error("At least two submissions are required for a comparison.")

    # Extract comparator and preprocessors from pass
    try:
        passes = [data.Pass._get(pass_) for pass_ in args.passes]
    except KeyError as e:
        raise errors.Error("{} is not a pass, try one of these: {}"\
                            .format(e.args[0], [c.__name__ for c in data.Pass._get_all()]))

    score_func = passes[0].comparator.score
    preprocessor = Preprocessor(passes[0].preprocessors)

    # TODO: remove this before we ship
    if args.profile:
        args.debug = True
        profiler = profile
    else:
        profiler = contextlib.suppress

    if args.debug:
        api.Executor = api.FauxExecutor
        # ProgressBar.DISABLED = True

    with profiler():
        try:
            api._PROGRESS_BAR = api._ProgressBar("Preparing")

            api.progress_bar()._start()
            # Collect all submissions, archive submissions and distro files
            subs = submission_factory.get_all(args.submissions, preprocessor)
            api.progress_bar().update(33)
            archive_subs = submission_factory.get_all(args.archive, preprocessor)
            api.progress_bar().update(33)
            ignored_subs = submission_factory.get_all(args.distro, preprocessor)
            ignored_files = [f for sub in ignored_subs for f in sub.files]

            # Cross compare and rank all submissions, keep only top `n`
            api.progress_bar().new_bar("Scoring")
            scores = api.rank(subs, archive_subs, ignored_files, passes[0].comparator, n=args.n)

            # Get the matching spans, group them per submission
            api.progress_bar().new_bar("Comparing")
            groups = []
            pass_to_results = {}
            for pass_ in passes:
                preprocessor = Preprocessor(pass_.preprocessors)
                for sub in subs + archive_subs + ignored_subs:
                    object.__setattr__(sub, "preprocessor", preprocessor)
                pass_to_results[pass_] = api.compare(scores, ignored_files, pass_.comparator)

            # Render results
            api.progress_bar().new_bar("Rendering")
            index = html_renderer.render(pass_to_results, dest=args.output)

        finally:
            api.progress_bar()._stop()
            api.__PROGRESS_BAR__ = None

        termcolor.cprint(f"Done! Visit file://{index.absolute()} in a web browser to see the results.", "green")

if __name__ == "__main__":
    main()
