from . import config
from . import api
from .data import Submission

if __name__ == "__main__":
    # TODO argparse for subs / archive / distro
    # TODO argparse for comparator
    c = config.get()
    comparator = c.comparator()
    preprocessors = c.preprocessors()

    # TODO argparse list all available comparators

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
