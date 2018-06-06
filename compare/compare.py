import pygments
import pygments.lexers
import pygments.lexers.special
from compare.token_processor import *
from compare.winnowing import Winnowing


# map pass names to (preprocessor, comparator) pairs
DEFAULT_CONFIG = {
    "strip_ws": (TokenProcessor(strip_whitespace),
                 Winnowing(16, 32)),
    "strip_all": (TokenProcessor(strip_whitespace,
                                 strip_comments,
                                 normalize_identifiers,
                                 normalize_string_literals),
                  Winnowing(10, 20, by_span=True))
}


def compare(preprocessor, comparator, submissions, distro=[], corpus=[]):
    """Compares a group of submissions to each other and to an optional
    other corpus using the provided preprocessor and
    processor. Returns a dict mapping pairs of submissions to scores
    """

    files = [] # list of all files
    groups = [] # list of lists of file ids
    group_of_file = [] # map file index to group index
    sub_groups = [] # map submission index to group index
    corpus_groups = [] # map corpus submission index to group index

    for f in distro:
        distro_ids.append(len(files))
        group_of_file.append(len(groups))
        files.append(f)
    groups.append(list(range(len(files))))

    for s in submissions:
        sub = []
        for f in s:
            sub.append(len(files))
            group_of_file.append(len(groups))
            files.append(f)
        sub_groups.append(len(groups))
        groups.append(sub)

    for s in corpus:
        sub = []
        for f in s:
            sub.append(len(files))
            group_of_file.append(len(groups))
            files.append(f)
        corpus_groups.append(len(groups))
        groups.append(sub)

    # single TextLexer instance to use for all plain text files
    text_lexer = pygments.lexers.special.TextLexer()

    def by_file_type(file_ids):
        """Take list of file ids and return dict mapping lexer name to list of
        (file, submission id, lexer) tuples"""
        results = {}
        for f in file_ids:
            # get lexer by filename, fallback to guessing then using text lexer
            try:
                lexer = pygments.lexers.get_lexer_for_filename(files[f])
            except pygments.util.ClassNotFound:
                try:
                    with open(files[f], "r") as file:
                        lexer = pygments.lexers.guess_lexer(file.read())
                except pygments.util.ClassNotFound:
                    lexer = text_lexer
            # use lexer name as proxy for file type
            results.setdefault(lexer.name, []).append((f, lexer))
        return results

    # pair each file with its submission index and lexer and split by file type
    distro_files = by_file_type(groups[0])
    sub_files = by_file_type([f for g in sub_groups for f in groups[g]])
    corpus_files = by_file_type([f for g in corpus_groups for f in groups[g]])

    # get deterministic ordering of file types (i.e. lexer names)
    file_types = list(set(distro_files.keys()) |
                      set(sub_files.keys()) |
                      set(corpus_files.keys()))

    # map submission pairs to score
    scores = {}

    # process one file type at a time
    for ftype in file_types:

        def make_index(typed_files):
            index = comparator.empty_index()
            for f, lexer in (typed_files.get(ftype) or []):
                text = preprocessor.process(f, files[f], lexer)
                index += comparator.create_index(f, text, group_of_file[f])
            return index

        distro_index = make_index(distro_files)
        sub_index = make_index(sub_files)
        corpus_index = make_index(corpus_files)

        # remove distro from indices and add submissions to corpus
        sub_index -= distro_index
        corpus_index -= distro_index
        corpus_index += sub_index

        # do comparison on indices
        ftype_scores, _ = sub_index.compare(corpus_index, 50)

        # update scores
        for sub_pair, score in ftype_scores:
            # TODO: do we need a more sophisticated way of combining scores
            # from different file types in for a single pass?
            scores.setdefault(sub_pair, 0)
            scores[sub_pair] += score

    # replace group IDs with tuples of files
    scores = {tuple(tuple(files[f] for f in groups[sub]) for sub in pair): score
              for pair, score in scores.items()}

    return scores
