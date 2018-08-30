import collections
import contextlib
import itertools
import pathlib
import re

import attr
from pygments.token import Comment

from .. import Comparator, Span, Comparison, Score


class Misspellings(Comparator):
    def __init__(self, dictionary):
        with open(dictionary) as f:
            self.dictionary = {s.strip() for s in f.readlines()}

    def _misspelled(self, *files):
        """Returns a set containing all of the words in each file that are not in the dictionary"""
        return set().union(*({tok.val for tok in file.tokens() if tok.val not in self.dictionary} for file in files))

    def score(self, submissions, archive_submissions, ignored_files):
        """Number of identically misspelled words."""
        ignored_words = self._misspelled(*ignored_files)

        # Map each submission to its misspelled words
        sub_to_words = {sub: self._misspelled(*sub) - ignored_words for sub in submissions}

        # For each pair of submissions, assign a score based upon number of misspelled words
        scores = [Score(sub_a, sub_b, _intersect_size(words_a, words_b))
                    for (sub_a, words_a), (sub_b, words_b) in itertools.combinations(sub_to_words.items(), r=2)]

        # Compare each archive submission against each regular submission
        for archive_sub in archive_submissions:
            # Find all misspelled words in archive
            archive_words = self._misspelled(*archive_sub) - ignored_words
            scores.extend(Score(sub, archive_sub, _intersect_size(words, archive_words))
                            for sub, words in sub_to_words.items())

        return scores

    def compare(self, scores, ignored_files):
        ignored_words = self._misspelled(*ignored_files)

        # Get all unique submissions to compare
        subs = set().union(*((s.sub_a, s.sub_b) for s in scores))

        # Spellcheck each file exactly once
        spellcheck_results = {file: self._spellcheck(file, ignored_words)
                                for sub in subs
                                    for file in sub}
        comparisons = []
        for score in scores:
            span_matches = []
            ignored_spans = set()
            for file_a, file_b in itertools.product(score.sub_a.files, score.sub_b.files):
                results_a, results_b = spellcheck_results[file_a], spellcheck_results[file_b]

                ignored_spans.update(results_a.correct, results_b.correct)
                span_matches.extend(results_a.match_misspellings(results_b))

            comparisons.append(Comparison(score.sub_a, score.sub_b,
                                          span_matches, list(ignored_spans)))
        return comparisons

    def _spellcheck(self, file, ignored_words):
        word_to_spans = collections.defaultdict(list)
        for token in file.tokens():
            word_to_spans[token.val].append(Span(file, token.start, token.end))

        result = SpellcheckResult()

        for word, spans in word_to_spans.items():
            if word in ignored_words or word in self.dictionary:
                result.correct.extend(spans)
            else:
                result.misspelled[word] = spans

        return result


@attr.s(slots=True)
class SpellcheckResult:
    # List of spans corresponding to correctly spelled words
    correct = attr.ib(factory=list)

    # Dict mapping misspelled words to spans
    misspelled = attr.ib(factory=dict)

    def match_misspellings(self, other):
        """Find all misspellings that self and other have in common and yield an iterable over all pairs of identical misspellings"""
        # Iterate over all keys of smaller dictionary for minor efficiency gain
        for word in min(self.misspelled, other.misspelled, key=len):
            with contextlib.suppress(KeyError):
                yield from itertools.product(self.misspelled[word], other.misspelled[word])


def _intersect_size(a, b):
    """Equivalent to len(a & b) but more efficient"""
    if len(b) < len(a):
        a, b = b, a

    return sum(item in b for item in a)
