import pygments
import pygments.lexers
import pygments.lexers.special
from compare.preprocessors.token_processor import *
from compare.comparators.winnowing import Winnowing


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


def compare(submissions, distro=[], corpus=[], config=DEFAULT_CONFIG):
    """Compares a group of submissions to each other and to an optional
    other corpus."""

    files = [] # list of all files
    groups = [] # lists of file ids
    group_of_file = [] # list of group ids
    sub_groups = [] # list of group ids
    corpus_groups = [] # list of group ids

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
            # get lexer by filename, fallback to text lexer
            try:
                lexer = pygments.lexers.get_lexer_for_filename(files[f])
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

    results = {}

    # process one file type and pass at a time to keep memory usage down
    for ftype in file_types:
        for pass_name, (preprocessor, comparator) in config.items():

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

            for sub_pair, score, span_pairs in sub_index.compare(corpus_index, 1000):
                # get previous score and spans for these submissions and pass
                entry = results.setdefault(sub_pair, {})
                old_score, old_span_pairs = entry.setdefault(pass_name, (0, []))
                # TODO: do we need a more sophisticated way of combining scores
                # from different file types in for a single pass?
                new_score = old_score + score
                new_span_pairs = old_span_pairs + span_pairs
                # update result score and span pairs
                results[sub_pair][pass_name] = (new_score, new_span_pairs)

    return files, groups, results
