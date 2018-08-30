import collections
import itertools
import pathlib
import re

from pygments.token import Comment

from .. import Comparator, Span, Comparison, Score


class Misspellings(Comparator):
    def __init__(self, dictionary):
        with open(dictionary) as f:
            self.dictionary = {s.strip() for s in f.readlines()}

    def _misspelled(self, tokens):
        return filter(lambda tok: tok.val not in self.dictionary, tokens)

    def score(self, submissions, archive_submissions, ignored_files):
        """Number of identically misspelled words."""
        ignored_words = set()
        for ignored_file in ignored_files:
            ignored_words |= {token.val for token in ignored_file.tokens()}

        sub_to_words = collections.defaultdict(set)
        for sub in submissions:
            for file in sub.files:
                sub_to_words[sub] |= {t.val for t in self._misspelled(file.tokens())} - ignored_words

        archive_sub_to_words = collections.defaultdict(set)
        for sub in archive_submissions:
            for file in sub.files:
                archive_sub_to_words[sub] |= {t.val for t in self._misspelled(file.tokens())} - ignored_words

        archive_sub_to_words.update(sub_to_words)

        scores = []
        for sub_a, words_a in sub_to_words.items():
            for sub_b, words_b in archive_sub_to_words.items():
                if sub_a == sub_b:
                    continue
                scores.append(Score(sub_a, sub_b, len(words_a & words_b)))
        return scores

    def compare(self, scores, ignored_files):
        ignored_words = set()
        for ignored_file in ignored_files:
            ignored_words |= {token.val for token in self._misspelled(ignored_file.tokens())}

        subs = set()
        for s in scores:
            subs.add(s.sub_a)
            subs.add(s.sub_b)

        # Spellcheck each file exactly once
        spellcheck_results = {file: self._spellcheck(file, ignored_words) for sub in subs for file in sub}

        comparisons = []
        for score in scores:
            span_matches = []
            ignored_spans = set()
            for file_a, file_b in itertools.product(score.sub_a.files, score.sub_b.files):
                misspelled_a, ignored_spans_a = spellcheck_results[file_a]
                misspelled_b, ignored_spans_b = spellcheck_results[file_b]
                ignored_spans.update(ignored_spans_a, ignored_spans_b)

                for word, (tokens_a, tokens_b) in _dict_intersect(misspelled_a, misspelled_b).items():
                    for token_a, token_b in itertools.product(tokens_a, tokens_b):
                        span_matches.append((Span(file_a, token_a.start, token_a.end),
                                             Span(file_b, token_b.start, token_b.end)))

            comparisons.append(Comparison(score.sub_a, score.sub_b, span_matches, list(ignored_spans)))
        return comparisons


    def _spellcheck(self, file, ignored_words):
        word_to_tokens = collections.defaultdict(list)
        for token in file.tokens():
            word_to_tokens[token.val].append(token)

        ignored_spans = []
        misspelled = {}

        for word, tokens in word_to_tokens.items():
            if word in ignored_words or word in self.dictionary:
                ignored_spans.extend(Span(file, token.start, token.end) for token in tokens)
            else:
                misspelled[word] = tokens

        return misspelled, ignored_spans


def _dict_intersect(a, b):
    """Construct a dict c such that for each key that a and b have in common, c[key] = (a[key], b[key])
    """

    # We are iterating over all keys in 'a', so let's make it the smaller one
    if len(b) < len(a):
        a, b = b, a

    intersection = {}
    for key, value in a.items():
        try:
            intersection[key] = (value, b[key])
        except KeyError:
            pass
    return intersection
