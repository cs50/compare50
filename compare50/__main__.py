from . import config
from . import api

if __name__ == "__main__":
    c = config.get()
    comparator = c.comparator()
    preprocessors = c.preprocessors()

    # TODO argparse for subs / archive / distro
    # TODO argparse for comparator
    # TODO argparse list all available comparators

    # TODO unzip subs/archive/distro if zip

    # TODO cross_compare, group by sub, rank, filter top n
    # submission_matches = api.rank_submissions(submissions, archive_submissions, ignored_files, comparator, n=50)

    # TODO create spans, group spans per sub_match
    # groups = api.create_groups(submission_matches, comparator)

    # TODO
    # html = api.render(groups)
