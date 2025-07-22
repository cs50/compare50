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


def partition(vals, pred):
    true = set()
    false = set()
    for val in vals:
        (true if pred(val) else false).add(val)
    return true, false


class SubmissionFactory:
    def __init__(self):
        self.max_file_size = 1024 * 1024
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

        # Ask lib50 which file(s) in path should be included
        if path.is_file():
            # lib50.files operates on a directory
            # So create a tempdir if the path is just a file
            with tempfile.TemporaryDirectory() as dir:
                (pathlib.Path(dir) / path.name).touch()
                included, excluded = lib50.files(self.patterns, root=dir)
            path = path.parent
        else:
            included, excluded = lib50.files(self.patterns, require_tags=[], root=path)

        # Filter out any non utf8 files
        decodable, undecodable = partition(included, lambda fp: self._is_valid_utf8(path / fp))

        # Filter out any large files (>self.max_file_size)
        small, large = partition(decodable, lambda fp: (path / fp).stat().st_size <= self.max_file_size)

        return _data.Submission(path, sorted(small),
                                large_files=sorted(large),
                                undecodable_files=sorted(undecodable),
                                preprocessor=preprocessor,
                                is_archive=is_archive)

    def get_all(self, paths, preprocessor, is_archive=False):
        """
        For every path, and every preprocessor, generate a Submission containing that path/preprocessor.
        Returns a list of lists of Submissions.
        """
        subs = set()
        for sub_path in paths:
            subs.add(self._get(sub_path, preprocessor, is_archive))
            _api.get_progress_bar().update()
        return subs

    @staticmethod
    def _is_valid_utf8(file_path):
        """
        Check if file_path is valid utf-8.
        f.read() is not performant since the entire file is read in before checking if it is valid utf8.
        This function reads in the file in increasingly large blocks so that it can error out early if necessary.
        """
        try:
            with open(file_path, encoding="utf8") as f:
                blocksize = 64
                while f.read(blocksize):
                    blocksize *= 2;
        except UnicodeDecodeError:
            return False
        return True


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
            print(str(pass_.__name__), f"(default: {'ON' if pass_.default else 'OFF'})")
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


def print_stats(subs, archives, distro_subs, distro_files, verbose=False):
    """
    Prints stats on the number of subs, archives, and distro files.
    Also prints a warning in case of any large and/or non utf-8 files.
    """

    def print_files(files, message):
        if not files:
            return

        termcolor.cprint(f"  {message}:", "yellow", attrs=["bold"])
        for file in files:
            termcolor.cprint(f"    {file}", "yellow", attrs=["bold"])

    def print_warning(sub_files, archive_files, distro_files, reason):
        print()
        data = PluralDict(subs=len(sub_files),
                          archives=len(archive_files),
                          distro=len(distro_files),
                          total=len(sub_files) + len(archive_files) + len(distro_files),
                          reason=reason)
        fmt = "Excluded {total} {reason} file{total(s)}: {subs} in submissions, " \
              "{archives} in archives, {distro} in distro"
        termcolor.cprint(fmt.format_map(data), "yellow", attrs=["bold"])

        # List all excluded large files in verbose mode
        if verbose:
            print_files(sub_files, f"{reason.capitalize()} files in submissions")
            print_files(archive_files, f"{reason.capitalize()} files in archives")
            print_files(distro_files, f"{reason.capitalize()} files in distro")

    def get_large_files(subs):
        return [sub.path / file for sub in subs for file in sub.large_files]

    def get_non_empty_subs(subs):
        return [sub for sub in subs if sub.files]

    def get_undecodable_files(subs):
        return [sub.path / file for sub in subs for file in sub.undecodable_files]

    # Print the number of subs, archives, distro files, and the average number of files per sub
    n_subs = len(get_non_empty_subs(subs))
    n_archives = len(get_non_empty_subs(archives))
    n_distro = len(distro_files)

    if n_subs + n_archives == 0:
        raise _api.Error(
            "No valid submissions found to compare.")

    avg = round(sum(len(s.files) for s in itertools.chain(subs, archives)) / (n_subs + n_archives), 2)
    data = PluralDict(subs=n_subs, archives=n_archives, distro=n_distro, avg=avg)
    fmt = "Found {subs} submission{subs(s)}, {archives} archive submission{archives(s)}, and " \
          "{distro} distro file{distro(s)} with an average of {avg} file{avg(s)} per submission"
    termcolor.cprint(fmt.format_map(data), "yellow", attrs=["bold"])

    # Keep track of any printed warning
    did_print_warning = False

    # Find all excluded large files
    large = get_large_files(subs)
    large_archive = get_large_files(archives)
    large_distro = get_large_files(distro_subs)

    # Warn about excluded large files
    if large or large_archive or large_distro:
        print_warning(large, large_archive, large_distro, "large")
        termcolor.cprint("  Consider increasing --max-file-size if these files should be included",
                         "yellow", attrs=["bold"])
        did_print_warning = True

    # Find all excluded undecodable (non utf-8) files
    undecodable = get_undecodable_files(subs)
    undecodable_archive = get_undecodable_files(archives)
    undecodable_distro = get_undecodable_files(distro_subs)

    # Warn about undecodable (non utf-8) files
    if undecodable or undecodable_archive or undecodable_distro:
        print_warning(undecodable, undecodable_archive, undecodable_distro, "non utf-8")
        did_print_warning = True

    # Print suggestion to run with --verbose if any files are excluded
    if not verbose and did_print_warning:
        termcolor.cprint("Rerun with --verbose to see which files are excluded",
                         "yellow", attrs=["bold"])


def expand_patterns(patterns):
    """
    Given a list of glob patterns, return a flat list containing the result
    of globbing all of them.
    """
    return list(itertools.chain.from_iterable(map(lambda x: glob.glob(x, recursive=True) or [x], patterns)))


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
                        default=[pass_.__name__ for pass_ in _data.Pass._get_all()
                                                if pass_.default],
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
    parser.add_argument("--max-file-size",
                        action="store",
                        default=1024,
                        type=int,
                        help="maximum allowed file size in KiB (default 1024 KiB)")
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

    # Set max file size in bytes
    submission_factory.max_file_size = args.max_file_size * 1024

    for attrib in ("submissions", "archive", "distro"):
        # Expand all patterns found in args.{submissions,archive,distro}
        setattr(args, attrib, expand_patterns(getattr(args, attrib)))

    # Extract comparator and preprocessors from pass
    try:
        passes = [_data.Pass._get(pass_) for pass_ in args.passes]
    except KeyError as e:
        raise _api.Error("{} is not a pass, try one of these: {}"
                           .format(e.args[0], [c.__name__ for c in _data.Pass._get_all()]))

    preprocessor = _data.Preprocessor(passes[0].preprocessors)

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

        print_stats(subs, archive_subs, ignored_subs, ignored_files, verbose=bool(args.verbose))

        # Remove any empty submissions
        subs = [sub for sub in subs if sub.files]
        archive_subs = [archive for archive in archive_subs if archive.files]

        # Not enough subs to compare, error
        if len(subs) + len(archive_subs) < 2:
            raise _api.Error("At least two non-empty submissions are required for a comparison.")

        with _api.progress_bar(f"Scoring ({passes[0].__name__})", disable=args.debug) as bar:
            # Cross compare and rank all submissions, keep only top `n`
            scores = _api.rank(subs, archive_subs, ignored_files, passes[0], n=args.n)

        # If ranking produced no scores, there are no matches, stop
        if not scores:
            termcolor.cprint(f"Done, no similarities found.", "yellow")
            return

        # Get the matching spans, group them per submission
        groups = []
        pass_to_results = {}
        for pass_ in passes:
            with _api.progress_bar(f"Comparing ({pass_.__name__})", disable=args.debug):
                preprocessor = _data.Preprocessor(pass_.preprocessors)
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
