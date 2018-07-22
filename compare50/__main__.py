import argparse
import textwrap
from . import config
from . import api
from . import errors
from .data import Submission

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

    # TODO argparse for subs / archive / distro

    # TODO unzip subs/archive/distro if zip

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
