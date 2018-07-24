import copy
import collections
import math
import numpy as np
import itertools
import attr

import concurrent.futures as futures

from compare50 import (
        preprocessors,
        Comparator,
        File, FileMatch,
        Pass,
        Span, SpanMatches,
)

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
                for file in sub.files():
                    yield file

        submissions_index = Index(self.k, self.t)
        archive_index = Index(self.k, self.t)

        with futures.ProcessPoolExecutor() as executor:
            for index in executor.map(self._index_file(self.k, self.t), iter_files(submissions)):
                submissions_index.include_all(index)

            for index in executor.map(self._index_file(self.k, self.t), iter_files(archive_submissions)):
                archive_index.include_all(index)

            for index in executor.map(self._index_file(self.k, self.t), ignored_files):
                submissions_index.ignore_all(index)
                archive_index.ignore_all(index)


        # Add submissions to archive (the Index we're going to compare against)
        archive_index.include_all(submissions_index)

        return submissions_index.compare(archive_index)

    def create_spans(self, file_matches, ignored_files):
        # for file_match in file_matches:
            # a_index = Index(self.k, self.t, complete=True)
            # b_index = Index(self.k, self.t, complete=True)

            # a_index.include(file_match.file_a)
            # b_index.include(file_match.file_b)

            # for file in ignored_files:
                # a_index.ignore(file)
                # b_index.ignore(file)

            # yield a_index.create_spans(b_index)

        with futures.ProcessPoolExecutor() as executor:
            return executor.map(self._create_spans(self.k, self.t, ignored_files), file_matches)

    @attr.s(slots=True)
    class _create_spans:
        k = attr.ib()
        t = attr.ib()
        ignored_files = attr.ib()

        def __call__(self, file_match):
            a_index = Index(self.k, self.t, complete=True)
            b_index = Index(self.k, self.t, complete=True)

            a_index.include(file_match.file_a)
            b_index.include(file_match.file_b)

            for file in self.ignored_files:
                a_index.ignore(file)
                b_index.ignore(file)

            return a_index.create_spans(b_index)

    @attr.s(slots=True)
    class _index_file:
        """ "Function" that indexes a file and returns the index.
        In the form of a class so that pickle can serialize it. """
        k = attr.ib()
        t = attr.ib()

        def __call__(self, file):
            index = Index(self.k, self.t)
            index.include(file)
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
    comparator = Winnowing(k=10, t=20)


class Index:
    __slots__ = ["k", "w", "_complete", "_index", "_max_id"]

    def __init__(self, k, t, complete=False):
        self.k = k
        self.w = t - k + 1
        self._complete = complete
        self._index = collections.defaultdict(set)
        self._max_id = 0

    def include(self, file):
        self._max_id = max(self._max_id, file.id)

        for hash, span in self._fingerprint(file):
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

        # Find common fingerprints (hashes)
        common_hashes = set(self._index) & set(other._index)
        for hash_ in common_hashes:
            # All spans associated with fingerprint in self
            spans_1 = self._index[hash_]
            # All spans associated with fingerprint in other
            spans_2 = other._index[hash_]

            return SpanMatches(itertools.product(spans_1, spans_2))


    def _fingerprint(self, file):
        tokens = file.tokens()

        if not tokens:
            return []

        kgrams = zip(*((tok.val for tok in tokens[i:]) for i in range(self.k)))
        hashes = (hash("".join(kgram)) for kgram in kgrams)

        starts = (tok.start for tok in tokens[:-self.k+1])
        ends = itertools.chain((tok.start for tok in tokens[self.k:]), (tokens[-1].end,))

        fingerprints = []
        if self._complete:
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
