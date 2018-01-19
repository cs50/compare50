import os
from itertools import chain
from preprocessors.nop import Nop
from preprocessors.token_processor import *
from comparators.winnowing import Winnowing
# map file extensions to lists of (preprocessor, comparator, weight) triples
CONFIG = {
    ".py": {
        "strip_ws": Winnowing(
            TokenProcessor(
                "Python3",
                StripWhitespace()),
            16, 32),
        "strip_all": Winnowing(
            TokenProcessor(
                "Python3",
                StripWhitespace(),
                StripComments(),
                NormalizeIdentifiers(),
                NormalizeStringLiterals()),
            10, 20, by_span=True)
    },
    ".c": {
        "strip_ws": Winnowing(
            TokenProcessor(
                "C",
                StripWhitespace()),
            16, 32),
        "strip_all": Winnowing(
            TokenProcessor(
                "C",
                StripWhitespace(),
                StripComments(),
                NormalizeIdentifiers(),
                NormalizeStringLiterals()),
            10, 20, by_span=True)
    },
    "default": {
        "default": Winnowing(Nop(), 20, 40)
    }
}


def compare(distro, submissions, corpus=[]):
    """Compares a group of submissions to each other and to an optional
    other corpus. Returns an ordered list of Results."""

    def by_extension(entries):
        results = {}
        for file, sub in entries:
            _, ext = os.path.splitext(file)
            if ext not in CONFIG.keys():
                ext = "default"
            results.setdefault(ext, []).append((file, sub))
        return results

    # pair each file with its submission index and split by extension
    distro_files = by_extension((file, 0) for file in distro)
    sub_files = by_extension((file, 1 + i)
                             for i, sub in enumerate(submissions)
                             for file in sub)
    corpus_files = by_extension((file, len(submissions) + 1 + i)
                                for i, sub in enumerate(corpus)
                                for file in sub)

    # get deterministic ordering of extensions
    extensions = list(set(distro_files.keys()) |
                      set(sub_files.keys()) |
                      set(corpus_files.keys()))

    def indices(files):
        indices = {ext: [] for ext in extensions}
        for ext in extensions:
            file_list = files.setdefault(ext, [])
            for name, comparator in CONFIG[ext].items():
                index = comparator.empty_index()
                for file, sub_id in file_list:
                    index += comparator.create_index(file, sub_id)
                indices[ext].append((index, name))
        return indices

    # create (index, weight) pairs for used file types
    distro_indices = indices(distro_files)
    sub_indices = indices(sub_files)
    corpus_indices = indices(corpus_files)

    # remove distro data from submissions
    for ext in extensions:
        index_sets = zip(distro_indices[ext],
                         sub_indices[ext],
                         corpus_indices[ext])
        for (distro_idx, _), (sub_idx, _), (corpus_idx, _) in index_sets:
            sub_idx -= distro_idx
            corpus_idx += sub_idx
            corpus_idx -= distro_idx

    # perform comparisons
    results = dict()
    for ext in extensions:
        index_pairs = zip(sub_indices[ext], corpus_indices[ext])
        for (sub_idx, pass_name), (corpus_idx, _) in index_pairs:
            for sub_pair, score, span_pairs in sub_idx.compare(corpus_idx):
                entry = results.setdefault(sub_pair, dict())
                entry = entry.setdefault(pass_name, (0, []))
                new_score = entry[0] + score
                new_span_pairs = entry[1] + span_pairs
                results[sub_pair][pass_name] = (new_score, new_span_pairs)

    # convert submission indices back into submission tuples for reporting
    combined_input = [distro] + submissions + corpus
    return {(combined_input[i], combined_input[j]): v
            for (i, j), v in results.items()}
