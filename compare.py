import os
from preprocessors.nop import Nop
from preprocessors.token_processor import *
from comparators.winnowing import Winnowing
from util import Match

# map file extensions to lists of (preprocessor, comparator, weight) triples
CONFIG = {
    ".py": [
        (Nop(), Winnowing(16, 32), 1),
        (TokenProcessor(
            "Python3",
            StripWhitespace(),
            StripComments(),
            NormalizeIdentifiers(),
            NormalizeStringLiterals()),
         Winnowing(10, 20), 1)
    ],
    ".c": [
        (Nop(), Winnowing(16, 32), 1),
        (TokenProcessor(
            "C",
            StripWhitespace(),
            StripComments(),
            NormalizeIdentifiers(),
            NormalizeStringLiterals()),
         Winnowing(10, 20), 1)
    ]
}


def compare(distro_path, submission_paths, corpus_paths=[]):
    """Compares a group of submissions to each other and to an optional
    other corpus. Returns an ordered list of Results."""
    _, extension = os.path.splitext(distro_path)

    def indices(path):
        with open(path, "r") as f:
            text = f.read()
        return [
            comparator.create_index(path, preprocessor.process(text))
            for preprocessor, comparator, _ in CONFIG[extension]
        ]
    distro_indices = indices(distro_path)

    # for each type of index, combine for all submission or corpus files
    submission_indices = [sum(idxs[1:], idxs[0]) for idxs in
                          zip(*[indices(path) for path in submission_paths])]
    corpus_indices = [sum(idxs[1:], idxs[0]) for idxs in
                      zip(*[indices(path) for path in corpus_paths])]

    # remove distro data from submissions
    for distro_idx, submission_idx in zip(distro_indices, submission_indices):
        submission_idx -= distro_idx

    # add submission and remove distro data to corpus if there is one
    if corpus_indices:
        index_classes = zip(distro_indices, submission_indices, corpus_indices)
        for distro_index, submission_index, corpus_index in index_classes:
            corpus_index += submission_index
            corpus_index -= distro_index
    else:
        corpus_indices = submission_indices

    # perform comparisons and combine results
    results = [s.compare(c)
               for s, c in zip(submission_indices, corpus_indices)]
    weights = [w for _, _, w in CONFIG[extension]]
    return Match.combine(results, weights=weights)
