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
            for token in ignored_file.tokens():
                ignored_words.add(token.val)

        subs = set()
        for s in scores:
            subs.add(s.sub_a)
            subs.add(s.sub_b)

        file_tokens = {}
        for sub in subs:
            for file in sub:
                file_tokens[file] = file.tokens()

        comparisons = []
        for score in scores:
            comparison = Comparison(score.sub_a, score.sub_b)
            for file_a, file_b in itertools.product(score.sub_a.files, score.sub_b.files):
                tokens_a, tokens_b = file_tokens[file_a], file_tokens[file_b]

                word_to_tokens_a = collections.defaultdict(list)
                for token in tokens_a:
                    word_to_tokens_a[token.val].append(token)

                word_to_tokens_b = collections.defaultdict(list)
                for token in tokens_b:
                    word_to_tokens_b[token.val].append(token)

                for word in ignored_words:
                    for token in word_to_tokens_a.get(word, []):
                        comparison.ignored_spans.append(Span(file_a, token.start, token.end))
                    for token in word_to_tokens_b.get(word, []):
                        comparison.ignored_spans.append(Span(file_b, token.start, token.end))

                common_misspellings = ({t.val for t in self._misspelled(tokens_a)}
                                        & {t.val for t in self._misspelled(tokens_b)}) - ignored_words

                for misspelling in common_misspellings:
                    ts_a = word_to_tokens_a[misspelling]
                    ts_b = word_to_tokens_b[misspelling]
                    for token_a, token_b in itertools.product(ts_a, ts_b):
                        comparison.span_matches.append((Span(file_a, token_a.start, token_a.end),
                                                        Span(file_b, token_b.start, token_b.end)))
            comparisons.append(comparison)

        return comparisons
