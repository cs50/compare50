import collections
import itertools
import pathlib
import re

from pygments.token import Comment

from .. import Comparator, Pass, Span, Token


class Misspellings(Comparator):
    def __init__(self, dictionary):
        with open(dictionary) as f:
            self.dictionary = {s.strip() for s in f.readlines()}

    def _misspelled_tokens(self, file):
        return [token for token in file.tokens() if token.val not in self.dictionary]

    def score(self, submissions, archive_submissions, ignored_files):
        ignored_words = set()
        for ignored_file in ignored_files:
            ignored_words |= {token.val for token in ignored_file.tokens()}

        sub_to_words = collections.defaultdict(set)
        for sub in submissions:
            for file in sub.files:
                sub_to_words[sub] |= {t.val for t in self._misspelled_tokens(file)} - ignored_words

        archive_sub_to_words = collections.defaultdict(set)
        for sub in archive_submissions:
            for file in sub.files:
                archive_sub_to_words[sub] |= {t.val for t in self._misspelled_tokens(file)} - ignored_words

        archive_sub_to_words.update(sub_to_words)

        sub_matches = []
        for sub_a, words_a in sub_to_words.items():
            for sub_b, words_b in archive_sub_to_words.items():
                if sub_a == sub_b:
                    continue
                sub_matches.append(SubmissionMatch(sub_a, sub_b, len(words_a & words_b)))
        return sub_matches

    def compare(self, file_pairs, ignored_files):
        ignored_words = set()
        for ignored_file in ignored_files:
            for token in ignored_file.tokens():
                ignored_words.add(token.val)

        ignored_spans_list = []
        span_matches_list = []
        file_to_tokens = {}
        for file_pair in file_pairs:
            file_a = file_pair.file_a
            file_b = file_pair.file_b

            ignored_spans_list.append(set())
            ignored_spans = ignored_spans_list[-1]

            if file_a not in file_to_tokens:
                file_to_tokens[file_a] = self._misspelled_tokens(file_a)
            tokens_a = file_to_tokens[file_a]

            if file_b not in file_to_tokens:
                file_to_tokens[file_b] = self._misspelled_tokens(file_b)
            tokens_b = file_to_tokens[file_b]

            word_to_tokens_a = collections.defaultdict(list)
            for token in tokens_a:
                word_to_tokens_a[token.val].append(token)
            word_to_tokens_b = collections.defaultdict(list)
            for token in tokens_b:
                word_to_tokens_b[token.val].append(token)

            for word in ignored_words:
                if word in word_to_tokens_a:
                    for token in word_to_tokens_a[word]:
                        ignored_spans.add(Span(file_a, token.start, token.end))
                if word in word_to_tokens_b:
                    for token in word_to_tokens_b[word]:
                        ignored_spans.add(Span(file_b, token.start, token.end))

            common_misspellings = ({t.val for t in tokens_a} & {t.val for t in tokens_b}) - ignored_words

            matches = []
            for misspelling in common_misspellings:
                ts_a = word_to_tokens_a[misspelling]
                ts_b = word_to_tokens_b[misspelling]
                for token_a, token_b in itertools.product(ts_a, ts_b):
                    matches.append((
                        Span(file_a, token_a.start, token_a.end),
                        Span(file_b, token_b.start, token_b.end)
                    ))
            if common_misspellings:
                span_matches_list.append(SpanMatches(matches))

        return zip(span_matches_list, ignored_spans_list)
