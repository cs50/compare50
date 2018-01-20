import pygments
import pygments.lexers
from preprocessors.token_processor import *
from comparators.winnowing import Winnowing


# map pass names to (preprocessor, comparator) pairs
# TODO: make configuration an optional parameter to `compare`
CONFIG = {
    "strip_ws": (TokenProcessor(strip_whitespace),
                 Winnowing(16, 32)),
    "strip_all": (TokenProcessor(strip_whitespace,
                                 strip_comments,
                                 normalize_identifiers,
                                 normalize_string_literals),
                  Winnowing(10, 20, by_span=True))
}


def compare(submissions, distro=None, corpus=[]):
    """Compares a group of submissions to each other and to an optional
    other corpus."""

    def by_file_type(entries):
        results = {}
        for file, sub in entries:
            # get lexer by filename, fallback to text lexer
            try:
                lexer = pygments.lexers.get_lexer_for_filename(file)
            except pygments.util.ClassNotFound:
                lexer = pygments.lexers.special.TextLexer()
            # use lexer name as proxy for file type
            results.setdefault(lexer.name, []).append((file, sub, lexer))
        return results

    # pair each file with its submission index and lexer and split by file type
    distro_files = by_file_type((file, 0) for file in distro) if distro else {}
    sub_files = by_file_type((file, 1 + i)
                             for i, sub in enumerate(submissions)
                             for file in sub)
    corpus_files = by_file_type((file, len(submissions) + 1 + i)
                                for i, sub in enumerate(corpus)
                                for file in sub)

    # get deterministic ordering of file types
    file_types = list(set(distro_files.keys()) |
                      set(sub_files.keys()) |
                      set(corpus_files.keys()))

    def indices(files):
        indices = {ftype: [] for ftype in file_types}
        for ftype in file_types:
            file_list = files.get(ftype) or []
            for pass_name, (preprocessor, comparator) in CONFIG.items():
                index = comparator.empty_index()
                for file, sub_id, lexer in file_list:
                    text = preprocessor.process(file, lexer)
                    index += comparator.create_index(file, text, sub_id)
                indices[ftype].append((index, pass_name))
        return indices

    # create list of (index, pass name) pairs for each file type
    distro_indices = indices(distro_files)
    sub_indices = indices(sub_files)
    corpus_indices = indices(corpus_files)

    # remove distro data from indices and add submission data to corpus data
    for ftype in file_types:
        index_sets = zip(distro_indices[ftype],
                         sub_indices[ftype],
                         corpus_indices[ftype])
        for (distro_idx, _), (sub_idx, _), (corpus_idx, _) in index_sets:
            sub_idx -= distro_idx
            corpus_idx += sub_idx
            corpus_idx -= distro_idx

    # perform comparisons between files of same type
    results = {}
    for ftype in file_types:
        index_pairs = zip(sub_indices[ftype], corpus_indices[ftype])
        for (sub_idx, pass_name), (corpus_idx, _) in index_pairs:
            for sub_pair, score, span_pairs in sub_idx.compare(corpus_idx):
                entry = results.setdefault(sub_pair, {})
                entry = entry.setdefault(pass_name, (0, []))
                # TODO: do we need a more sophisticated way of combining scores
                # from different file types in for a single pass?
                new_score = entry[0] + score
                new_span_pairs = entry[1] + span_pairs
                results[sub_pair][pass_name] = (new_score, new_span_pairs)

    # convert submission indices back into submission tuples
    combined_input = [distro] + submissions + corpus
    return {(combined_input[i], combined_input[j]): v
            for (i, j), v in results.items()}
