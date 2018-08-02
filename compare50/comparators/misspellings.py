import copy
import collections
import math
import numpy as np
import itertools
import attr
import pathlib
import re
from pygments.token import Token as PygToken
import concurrent.futures as futures

from compare50 import (
        preprocessors,
        Comparator,
        File, FileMatch,
        Pass,
        Span, SpanMatches, Token
)

def words(tokens):
    for t in tokens:
        if t.type == PygToken.Comment.Single or t.type == PygToken.Comment.Multiline:
            start = t.start
            only_alpha = re.sub("[^a-zA-Z'_-]", " ", t.val)
            for val, (start, end) in [(m.group(0), (m.start(), m.end())) for m in re.finditer(r'\S+', only_alpha)]:
                yield Token(t.start + start, t.start + end, t.type, val)

def lowercase(tokens):
    for t in tokens:
        t.val = t.val.lower()
        yield t

class Misspellings(Comparator):
    def __init__(self, dictionary):
        with open(dictionary) as f:
            self.dictionary = {s.strip() for s in f.readlines()}

    def _misspelled_tokens(self, file):
        return [token for token in file.tokens() if token.val not in self.dictionary]

    def cross_compare(self, submissions, archive_submissions, ignored_files):
        ignored_words = set()
        for ignored_file in ignored_files:
            ignored_words |= {token.val for token in ignored_file.tokens()}

        file_to_words = {}
        for sub in submissions:
            for file in sub.files:
                file_to_words[file] = {t.val for t in self._misspelled_tokens(file)} - ignored_words

        archive_file_to_words = {}
        for sub in archive_submissions:
            for file in sub.files:
                archive_file_to_words[file] = {t.val for t in self._misspelled_tokens(file)} - ignored_words

        file_matches = []
        for file_a, words_a in file_to_words.items():
            for file_b, words_b in file_to_words.items():
                if file_a == file_b:
                    continue
                file_matches.append(FileMatch(file_a, file_b, len(words_a & words_b)))
        return file_matches

    def create_spans(self, file_matches, ignored_files):
        ignored_words = set()
        for ignored_file in ignored_files:
            ignored_words += {token.val for token in ignored_file.tokens()}

        span_matches = []
        file_to_tokens = {}
        for file_match in file_matches:
            if file_match.file_a not in file_to_tokens:
                file_to_tokens[file_match.file_a] = self._misspelled_tokens(file_match.file_a)
            tokens_a = file_to_tokens[file_match.file_a]

            if file_match.file_b not in file_to_tokens:
                file_to_tokens[file_match.file_b] = self._misspelled_tokens(file_match.file_b)
            tokens_b = file_to_tokens[file_match.file_b]

            # tokens_a = self._misspelled_tokens(file_match.file_a)
            # tokens_b = self._misspelled_tokens(file_match.file_b)

            word_to_tokens_a = collections.defaultdict(list)
            for token in tokens_a:
                word_to_tokens_a[token.val].append(token)
            word_to_tokens_b = collections.defaultdict(list)
            for token in tokens_b:
                word_to_tokens_b[token.val].append(token)

            common_misspellings = ({t.val for t in tokens_a} & {t.val for t in tokens_b}) - ignored_words
            matches = []
            for misspelling in common_misspellings:
                ts_a = word_to_tokens_a[misspelling]
                ts_b = word_to_tokens_b[misspelling]
                for token_a, token_b in itertools.product(ts_a, ts_b):
                    matches.append((
                        Span(file_match.file_a, token_a.start, token_a.end),
                        Span(file_match.file_b, token_b.start, token_b.end)
                    ))
            if common_misspellings:
                span_matches.append(SpanMatches(matches))

        return span_matches

class EnglishMisspellings(Pass):
    description = "Compare for english word misspellings."
    preprocessors = [words, lowercase]
    comparator = Misspellings(pathlib.Path(__file__).parent / "english_dictionary.txt")
