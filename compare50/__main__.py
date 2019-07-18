import argparse
import contextlib
import glob
import itertools
import os
import pathlib
import tempfile
import textwrap
import shutil
import sys
import string
import traceback
import time
import tempfile

import attr
import lib50
import termcolor

from . import comparators, _api, _data, _renderer, __version__


def excepthook(cls, exc, tb):
    if (issubclass(cls, _api.Error) or issubclass(cls, lib50.Error)) and exc.args:
        termcolor.cprint(str(exc), "red", file=sys.stderr)
    elif cls is FileNotFoundError:
        termcolor.cprint("{} not found".format(exc.filename), "red", file=sys.stderr)
    elif not issubclass(cls, Exception) and not isinstance(exc, KeyboardInterrupt):
        # Class is some other BaseException, better just let it go
        return
    elif isinstance(exc, KeyboardInterrupt):
        print()
    else:
        termcolor.cprint(
            "Sorry, something's wrong! Let sysadmins@cs50.harvard.edu know!", "red", file=sys.stderr)

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
        pattern = lib50.config.TaggedValue(pattern, "include")
        self.patterns.append(pattern)

    def exclude(self, pattern):
        pattern = lib50.config.TaggedValue(pattern, "exclude")
        self.patterns.append(pattern)

    def _get(self, path, preprocessor, is_archive=False):
        path = pathlib.Path(path)

        if path.is_file():
            with tempfile.TemporaryDirectory() as dir:
                (pathlib.Path(dir) / path.name).touch()
                included, excluded = lib50.files(self.patterns, root=dir)
            path = path.parent
        else:
            included, excluded = lib50.files(self.patterns, require_tags=[], root=path)

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
            raise _api.Error(f"Empty submission: {path}")

        decodable_files = sorted(decodable_files)
        return _data.Submission(path, decodable_files, preprocessor=preprocessor, is_archive=is_archive)

    def get_all(self, paths, preprocessor, is_archive=False):
        """
        For every path, and every preprocessor, generate a Submission containing that path/preprocessor.
        Returns a list of lists of Submissions.
        """
        subs = set()
        for sub_path in paths:
            try:
                subs.add(self._get(sub_path, preprocessor, is_archive))
            except _api.Error:
                pass
            else:
                _api.get_progress_bar().update()
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
        for pass_ in _data.Pass._get_all():
            print(str(pass_.__name__))
            for line in textwrap.wrap(pass_.__doc__ or "No description provided", 80 - len(indentation)):
                print("{}{}".format(indentation, line))
        parser.exit()


class IncludeExcludeAction(argparse.Action):
    """Hook into argparse to allow ordering of include/exclude."""

    def __init__(self, option_strings, callback=None, **kwargs):
        super().__init__(option_strings, **kwargs)
        if not callback:
            raise RuntimeError("IncludeExcludeAction requires a callback.")
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


PROFILE = [ _api.compare
          , comparators.Winnowing.score
          , comparators.Winnowing.compare
          , comparators._winnowing.Index.hashes
          , comparators._winnowing.CompareIndex.fingerprint
          , comparators._winnowing.ScoreIndex.fingerprint
          , _renderer.render
          ]


@contextlib.contextmanager
def profile():
    import termcolor
    import time
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


# https://stackoverflow.com/questions/21872366/plural-string-formatting
class PluralDict(dict):
    def __missing__(self, key):
        if '(' in key and key.endswith(')'):
            key, rest = key.split('(', 1)
            value = super().__getitem__(key)
            suffix = rest.rstrip(')').split(',')
            if len(suffix) == 1:
                suffix.insert(0, '')
            return suffix[0] if value == 1 else suffix[1]
        raise KeyError(key)


def print_stats(subs, archives, distro_files):
    avg = round(sum(len(s.files) for s in itertools.chain(subs, archives)) / (len(subs) + len(archives)), 2)
    data = PluralDict(subs=len(subs), archives=len(archives), distro=len(distro_files), avg=avg)
    fmt = "Found {subs} submission{subs(s)}, {archives} archive submission{archives(s)}, and " \
          "{distro} distro file{distro(s)} with an average of {avg} file{avg(s)} per submission"
    termcolor.cprint(fmt.format_map(data), "yellow", attrs=["bold"])


def expand_patterns(patterns):
    """
    Given a list of glob patterns, return a flat list containing the result
    of globbing all of them.
    """
    return list(itertools.chain.from_iterable(map(lambda x: glob.glob(x, recursive=True), patterns)))


def main():
    submission_factory = SubmissionFactory()

    parser = ArgParser(prog="compare50")
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
                        default=[pass_.__name__ for pass_ in _data.Pass._get_all()],
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
    parser.add_argument("--list",
                        action=ListAction)
    parser.add_argument("-o", "--output",
                        action="store",
                        default="results",
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
    parser.add_argument("--profile",
                        action="store_true",
                        help="profile compare50 (development only, requires line_profiler, implies debug)")
    parser.add_argument("--debug",
                        action="store_true",
                        help="don't run anything in parallel, disable progress bar")
    parser.add_argument("-V", "--version",
                        action="version",
                        version=f"%(prog)s {__version__}")

    args = parser.parse_args()

    excepthook.verbose = args.verbose

    for attrib in ("submissions", "archive", "distro"):
        # Expand all patterns found in args.{submissions,archive,distro}
        setattr(args, attrib, expand_patterns(getattr(args, attrib)))


    # Extract comparator and preprocessors from pass
    try:
        passes = [_data.Pass._get(pass_) for pass_ in args.passes]
    except KeyError as e:
        raise _api.Error("{} is not a pass, try one of these: {}"
                           .format(e.args[0], [c.__name__ for c in _data.Pass._get_all()]))

    preprocessor = Preprocessor(passes[0].preprocessors)

    if args.profile:
        args.debug = True
        profiler = profile
    else:
        profiler = contextlib.suppress

    if args.debug:
        _api.Executor = _api.FauxExecutor

    if args.output.exists():
        try:
            resp = input(f"File path {termcolor.colored(args.output, None, attrs=['underline'])}"
                          " already exists. Do you want to remove it? [Y/n] ")
        except EOFError:
            resp = "n"
            print()

        if not resp or resp.lower().startswith("y"):
            try:
                os.remove(args.output)
            except (IsADirectoryError, PermissionError):
                shutil.rmtree(args.output)
        else:
            print("Quitting...")
            sys.exit(1)

    with profiler():
        total = len(args.submissions) + len(args.archive) + len(args.distro)
        with _api.progress_bar("Preparing", total=total, disable=args.debug) as bar:
            # Collect all submissions, archive submissions and distro files
            subs = submission_factory.get_all(args.submissions, preprocessor)
            archive_subs = submission_factory.get_all(args.archive, preprocessor, is_archive=True)
            ignored_subs = submission_factory.get_all(args.distro, preprocessor)
            ignored_files = {f for sub in ignored_subs for f in sub.files}

            if len(subs) + len(archive_subs) < 2:
                raise _api.Error("At least two non-empty submissions are required for a comparison.")

        print_stats(subs, archive_subs, ignored_files)

        with _api.progress_bar(f"Scoring ({passes[0].__name__})", disable=args.debug) as bar:
            # Cross compare and rank all submissions, keep only top `n`
            scores = _api.rank(subs, archive_subs, ignored_files, passes[0], n=args.n)

        # Get the matching spans, group them per submission
        groups = []
        pass_to_results = {}
        for pass_ in passes:
            with _api.progress_bar(f"Comparing ({pass_.__name__})", disable=args.debug):
                preprocessor = Preprocessor(pass_.preprocessors)
                for sub in itertools.chain(subs, archive_subs, ignored_subs):
                    object.__setattr__(sub, "preprocessor", preprocessor)
                pass_to_results[pass_] = _api.compare(scores, ignored_files, pass_)

        # Render results
        with _api.progress_bar("Rendering", disable=args.debug):
            index = _renderer.render(pass_to_results, dest=args.output)

    termcolor.cprint(
        f"Done! Visit file://{index.absolute()} in a web browser to see the results.", "green")


if __name__ == "__main__":
    main()
