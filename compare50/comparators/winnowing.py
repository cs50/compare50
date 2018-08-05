import copy
import collections
import math
import numpy as np
import itertools
import attr
import time
import multiprocessing

import concurrent.futures as futures

from .. import api

from compare50 import (
        preprocessors,
        Comparator,
        File, FileMatch,
        Pass,
        Span, SpanMatches,
)

class FauxExecutor:
    def map(self, fn, *iterables, timeout=None, chunksize=1):
        for iterable in iterables:
            for res in map(fn, iterable):
                yield res

    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        return


def ignore(file, ignored_index, tokens=None):
    if tokens is None:
        tokens = file.tokens()

    # Nothing to ignore
    if not ignored_index:
        return [tokens]

    # Create an index of file with same settings as ignored_index
    index = Index(k=ignored_index.k, t=ignored_index.t, complete=ignored_index.complete)
    index.include(file, tokens=tokens)

    # Figure out spans (regions) of the file to ignore
    # Note: these can overlap!
    ignored_spans = sorted(index.common_spans(ignored_index), key=lambda span: span.start)

    # Nothing to ignore
    if not ignored_spans:
        return [tokens]

    # Find relevant tokens (any token not completely in an ignored_span)
    relevant_token_lists = []
    relevant_tokens = []
    i = 0
    span_iter = iter(ignored_spans)
    span = next(span_iter)
    for i, token in enumerate(tokens):
        # If token comes after span, move on to next span
        while token.end > span.end:
            try:
                span = next(span_iter)
            except StopIteration:
                relevant_token_lists.append(relevant_tokens + tokens[i:])
                return relevant_token_lists

        # If token starts before the span does, it's relevant
        if token.start < span.start:
            relevant_tokens.append(token)
        # If a token is ignored, yield any relevant_tokens so far
        elif relevant_tokens:
            relevant_token_lists.append(relevant_tokens)
            relevant_tokens = []

    return relevant_token_lists

class Winnowing(Comparator):
    """ Comparator utilizing the (robust) Winnowing algorithm as described https://theory.stanford.edu/~aiken/publications/papers/sigmod03.pdf

    :param t: the guarantee threshold; any matching sequence of tokens of length at least t is guaranteed to be matched
    :type t: int
    :parma k: the noise threshold; any matching sequence of tokens shorter than this will be ignored
    :type k: int
    """

    __slots__ = ["k", "t"]

    def __init__(self, k, t):
        self.k = k
        self.t = t

    def cross_compare(self, submissions, archive_submissions, ignored_files):
        """"""
        def iter_files(subs):
            for sub in subs:
                for file in sub:
                    yield file

        submissions_index = Index(self.k, self.t)
        archive_index = Index(self.k, self.t)

        with futures.ProcessPoolExecutor() as executor:
            ignored_index = Index(self.k, self.t)
            for index in executor.map(self._index_file(self.k, self.t), ignored_files):
                ignored_index.include_all(index)

            for index in executor.map(self._index_file(self.k, self.t, ignored_index), iter_files(submissions)):
                submissions_index.include_all(index)

            for index in executor.map(self._index_file(self.k, self.t, ignored_index), iter_files(archive_submissions)):
                archive_index.include_all(index)

        # Add submissions to archive (the Index we're going to compare against)
        archive_index.include_all(submissions_index)

        return submissions_index.compare(archive_index)

    def create_spans(self, file_matches, ignored_files):
        with futures.ProcessPoolExecutor() as executor:
            ignored_index = Index(self.k, self.t, complete=True)
            for ignored_i in executor.map(self._index_file(self.k, self.t, complete=True), ignored_files):
                ignored_index.include_all(ignored_i)

            # Find all unique files
            files = set()
            for fm in file_matches:
                files.add(fm.file_a)
                files.add(fm.file_b)

            # Tokenize all files
            file_tokens = {}
            for file in files:
                file_tokens[file] = file.tokens()

            return executor.map(self._create_spans(self.k, self.t, ignored_index),
                                ((fm, file_tokens[fm.file_a], file_tokens[fm.file_b]) for fm in file_matches))

    @attr.s(slots=True)
    class _create_spans:
        k = attr.ib()
        t = attr.ib()
        ignored_index = attr.ib()

        def __call__(self, match):
            file_match, original_tokens_a, original_tokens_b = match

            file_a = file_match.file_a
            file_b = file_match.file_b

            # List of list of tokens (each list is uninterupted by ignored content)
            token_lists_a = ignore(file_a, self.ignored_index, tokens=original_tokens_a)
            token_lists_b = ignore(file_b, self.ignored_index, tokens=original_tokens_b)

            indices_a = [Index(self.k, self.t, complete=self.ignored_index.complete) for ts in token_lists_a]
            indices_b = [Index(self.k, self.t, complete=self.ignored_index.complete) for ts in token_lists_b]

            for index_a, tokens_a in zip(indices_a, token_lists_a):
                index_a.include(file_a, tokens=tokens_a)

            for index_b, tokens_b in zip(indices_b, token_lists_b):
                index_b.include(file_b, tokens=tokens_b)

            ignored_spans = \
                api.missing_spans(
                    file_a,
                    original_tokens=original_tokens_a,
                    preprocessed_tokens=list(itertools.chain.from_iterable(token_lists_a)))
            ignored_spans.extend(
                api.missing_spans(
                    file_b,
                    original_tokens=original_tokens_b,
                    preprocessed_tokens=list(itertools.chain.from_iterable(token_lists_b))))

            span_matches = SpanMatches()
            for index_a, tokens_a in zip(indices_a, token_lists_a):
                for index_b, tokens_b in zip(indices_b, token_lists_b):
                    sm = index_a.create_spans(index_b)
                    sm.expand(tokens_a, tokens_b)
                    span_matches += sm

            return span_matches, ignored_spans

    @attr.s(slots=True)
    class _index_file:
        """ "Function" that indexes a file and returns the index.
        In the form of a class so that pickle can serialize it. """
        k = attr.ib()
        t = attr.ib()
        ignored_index = attr.ib(default=None)
        complete=attr.ib(default=False)

        def __call__(self, file):
            index = Index(self.k, self.t, complete=self.complete)
            index.include(file)
            if self.ignored_index:
                index.ignore_all(self.ignored_index)
            return index


class StripWhitespace(Pass):
    description = "Remove all whitespace, then run Winnowing with k=16, t=32."
    preprocessors = [preprocessors.strip_whitespace, preprocessors.by_character]
    comparator = Winnowing(k=16, t=32)


class StripAll(Pass):
    description = "Remove all whitespace, norm all comments/ids/strings, then run Winnowing with k=10, t=20."
    preprocessors = [preprocessors.strip_whitespace,
                     preprocessors.strip_comments,
                     preprocessors.normalize_identifiers,
                     preprocessors.normalize_string_literals]
    comparator = Winnowing(k=16, t=32)


class Index:
    __slots__ = ["k", "t", "w", "complete", "_index", "_max_id"]

    def __init__(self, k, t, complete=False):
        self.k = k
        self.t = t
        self.w = t - k + 1
        self.complete = complete
        self._index = collections.defaultdict(set)
        self._max_id = 0

    def include(self, file, tokens=None):
        self._max_id = max(self._max_id, file.id)
        for hash, span in self._fingerprint(file, tokens):
            self._index[hash].add(span)

    def ignore(self, file):
        for hash, _ in self._fingerprint(file):
            self._index.pop(hash, None)

    def include_all(self, other):
        for hash, spans in other._index.items():
            self._index[hash] |= spans
        self._max_id = max(self._max_id, other._max_id)
        return self

    def ignore_all(self, other):
        for hash in other._index:
            self._index.pop(hash, None)

    def compare(self, other):
        # Validate other index
        if self.k != other.k:
            raise RuntimeError("comparison with different n-gram lengths")

        # Keep a self.max_file_id by other.max_file_id matrix for counting score
        scores = np.zeros((self._max_id + 1, other._max_id + 1))

        # Find common fingerprints (hashes)
        common_hashes = set(self._index) & set(other._index)
        for hash_ in common_hashes:
            # All file_ids associated with fingerprint in self
            index1 = self._index[hash_]
            # All file_ids associated with fingerprint in other
            index2 = other._index[hash_]
            if index1 and index2:
                # Create the product of all file_ids from self and other
                # https://stackoverflow.com/questions/28684492/numpy-equivalent-of-itertools-product
                index = np.array(np.meshgrid([span.file.id for span in index1],
                                             [span.file.id for span in index2])).T.reshape(-1, 2)
                # index = index[index[:,0] < index[:,1]]

                # Add 1 to all combo's (the product) of file_ids from self and other
                scores[index[:,0], index[:,1]] += 1

        # Return only those FileMatches with a score > 0 from different submissions
        return [FileMatch(File.get(id1), File.get(id2), scores[id1][id2])
                for id1, id2 in zip(*np.where(np.triu(scores, 1) > 0))]

    def create_spans(self, other):
        # Validate other index
        if self.k != other.k:
            raise RuntimeError("comparison with different n-gram lengths")

        matches = []

        # Find common fingerprints (hashes)
        common_hashes = set(self._index) & set(other._index)
        for hash_ in common_hashes:
            # All spans associated with fingerprint in self
            spans_1 = self._index[hash_]
            # All spans associated with fingerprint in other
            spans_2 = other._index[hash_]
            matches.extend(itertools.product(spans_1, spans_2))

        span_matches = SpanMatches(matches)
        return span_matches

    def common_spans(self, other):
        spans = set()
        for hash_ in set(self._index) & set(other._index):
            spans |= self._index[hash_]
            spans |= other._index[hash_]
        return spans

    def _fingerprint(self, file, tokens=None):
        if not tokens:
            tokens = file.tokens()
            if not tokens:
                return []

        kgrams = zip(*((tok.val for tok in tokens[i:]) for i in range(self.k)))
        hashes = (hash("".join(kgram)) for kgram in kgrams)

        starts = (tok.start for tok in tokens[:-self.k+1])
        ends = itertools.chain((tok.start for tok in tokens[self.k:]), (tokens[-1].end,))

        fingerprints = []
        if self.complete:
            # use all fingerprints instead of sampling
            for start, end, hash_ in zip(starts, ends, hashes):
                fingerprints.append((hash_, Span(file, start, end)))
        else:
            # circular buffer holding window
            buf = [(math.inf, Span(None, 0, 0))] * self.w
            # index of minimum hash in buffer
            min_idx = 0
            for start, end, hash_, idx in zip(starts, ends, hashes, itertools.cycle(range(self.w))):
                buf[idx] = hash_, Span(file, start, end)
                if min_idx == idx:
                    # old min not in window, search left for new min
                    for j in range(1, self.w):
                        search_idx = (idx - j) % self.w
                        if buf[search_idx][0] < buf[min_idx][0]:
                            min_idx = search_idx
                    fingerprints.append(buf[min_idx])
                else:
                    # compare new hash to old min (robust winnowing)
                    if buf[idx][0] < buf[min_idx][0]:
                        min_idx = idx
                        fingerprints.append(buf[min_idx])
        return fingerprints

    def __bool__(self):
        return len(self._index) != 0
