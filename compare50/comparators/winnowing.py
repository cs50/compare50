import abc
import collections
import math
import itertools
import concurrent.futures as futures

import attr
import numpy as np

from .. import (
    api,
    preprocessors,
    Comparator,
    File, Submission, SubmissionMatch,
    Pass,
    Span, SpanMatch,
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

    def score(self, submissions, archive_submissions, ignored_files):
        """"""
        def iter_files(subs):
            for sub in subs:
                for file in sub:
                    yield file

        submissions_index = CrossCompareIndex(self.k, self.t)
        archive_index = CrossCompareIndex(self.k, self.t)

        with api.Executor() as executor:
            ignored_index = CrossCompareIndex(self.k, self.t)
            for index in executor.map(self._index_file(CrossCompareIndex, (self.k, self.t)), ignored_files):
                ignored_index.include_all(index)

            for index in executor.map(self._index_file(CrossCompareIndex, (self.k, self.t)), iter_files(submissions)):
                submissions_index.include_all(index)
            submissions_index.ignore_all(ignored_index)

            for index in executor.map(self._index_file(CrossCompareIndex, (self.k, self.t)), iter_files(archive_submissions)):
                archive_index.include_all(index)
            archive_index.ignore_all(ignored_index)

        # Add submissions to archive (the Index we're going to compare against)
        archive_index.include_all(submissions_index)

        return submissions_index.compare(archive_index)

    def compare(self, submission_matches, ignored_files):
        ignored_index = CompareIndex(self.k)
        for ignored_i in map(self._index_file(CompareIndex, (self.k,)), ignored_files):
            ignored_index.include_all(ignored_i)

        # Find all unique submissions
        subs = set()
        for sm in submission_matches:
            subs.add(sm.sub_a)
            subs.add(sm.sub_b)

        # Tokenize all files
        file_tokens = {}
        for sub in subs:
            for file in sub:
                file_tokens[file] = file.tokens()

        return map(self._create_spans(self.k, self.t, ignored_index, file_tokens), submission_matches)

    @attr.s(slots=True)
    class _create_spans:
        k = attr.ib()
        t = attr.ib()
        ignored_index = attr.ib()
        file_tokens = attr.ib()

        def __call__(self, submission_match):
            sub_a = submission_match.sub_a
            sub_b = submission_match.sub_b

            ignored_spans = []

            file_to_token_lists = {}
            file_to_indices = {}

            for file in sub_a.files + sub_b.files:
                # List of list of tokens (each list is uninterupted by ignored content)
                token_lists = self.ignored_index.unignored_tokens(file, tokens=self.file_tokens[file])
                file_to_token_lists[file] = token_lists

                indices = [CompareIndex(self.k) for ts in token_lists]
                file_to_indices[file] = indices

                for index, tokens in zip(indices, token_lists):
                    index.include(file, tokens=tokens)

                ignored_spans += api.missing_spans(file,
                                                   original_tokens=self.file_tokens[file],
                                                   preprocessed_tokens=list(itertools.chain.from_iterable(token_lists)))

            span_matches = []
            for file_a, file_b in itertools.product(sub_a.files, sub_b.files):
                indices_a = file_to_indices[file_a]
                indices_b = file_to_indices[file_b]

                token_lists_a = file_to_token_lists[file_a]
                token_lists_b = file_to_token_lists[file_b]

                for index_a, tokens_a in zip(indices_a, token_lists_a):
                    for index_b, tokens_b in zip(indices_b, token_lists_b):
                        matches = index_a.compare(index_b)
                        matches = api.expand(matches, tokens_a, tokens_b)
                        span_matches += matches

            return span_matches, ignored_spans

    @attr.s(slots=True)
    class _index_file:
        """ "Function" that indexes a file and returns the index.
        In the form of a class so that pickle can serialize it. """
        index = attr.ib()
        args = attr.ib(default=())

        def __call__(self, file):
            index = self.index(*self.args)
            index.include(file)
            return index


class Index(abc.ABC):
    def __init__(self, k):
        self.k = k
        self._index = collections.defaultdict(set)

    def include(self, file, tokens=None):
        for hash, val in self.fingerprint(file, tokens):
            self._index[hash].add(val)

    def include_all(self, other):
        for hash, vals in other._index.items():
            self._index[hash] |= vals
        return self

    def ignore_all(self, other):
        for hash in other._index:
            self._index.pop(hash, None)

    def kgrams(self, iterable):
        iters = itertools.tee(iterable, self.k)
        for i, it in enumerate(iters):
            next(itertools.islice(it, i, i), None)
        return zip(*iters)

    def hashes(self, tokens):
        return (hash("".join(kgram)) for kgram in self.kgrams((t.val for t in tokens)))

    @abc.abstractmethod
    def compare(self, other):
        pass

    @abc.abstractmethod
    def fingerprint(self, file, tokens=None):
        pass

    def __bool__(self):
        return bool(self._index)


class CrossCompareIndex(Index):
    def __init__(self, k, t):
        super().__init__(k)
        self.t = t
        self.w = t - k + 1
        self._max_id = 0

    def include(self, file, tokens=None):
        super().include(file, tokens)
        self._max_id = max(self._max_id, file.submission.id)

    def include_all(self, other):
        super().include_all(other)
        self._max_id = max(self._max_id, other._max_id)

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
                index = np.array(np.meshgrid([id for id in index1],
                                             [id for id in index2])).T.reshape(-1, 2)

                # Add 1 to all combo's (the product) of file_ids from self and other
                scores[index[:,0], index[:,1]] += 1

        # Return only those FileMatches with a score > 0 from different submissions
        return [SubmissionMatch(Submission.get(id1), Submission.get(id2), scores[id1][id2])
                for id1, id2 in zip(*np.where(np.triu(scores, 1) > 0))]

    def fingerprint(self, file, tokens=None):
        if not tokens:
            tokens = file.tokens()
            if not tokens:
                return []

        hashes = self.hashes(tokens)

        fingerprints = []

        # circular buffer holding window
        buf = [(math.inf, Span(None, 0, 0))] * self.w
        # index of minimum hash in buffer
        min_idx = 0
        for hash_, idx in zip(hashes, itertools.cycle(range(self.w))):
            buf[idx] = hash_, file.submission.id
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


class CompareIndex(Index):
    def compare(self, other):
        # Validate other index
        if self.k != other.k:
            raise RuntimeError("comparison with different n-gram lengths")

        matches = []

        # Find common fingerprints (hashes)
        common_hashes = set(self._index) & set(other._index)
        for hash_ in common_hashes:
            # All spans associated with fingerprint in self
            spans_a = self._index[hash_]
            # All spans associated with fingerprint in other
            spans_b = other._index[hash_]
            matches.extend(SpanMatch(span_a, span_b) for span_a, span_b in itertools.product(spans_a, spans_b))

        return matches

    def common_spans(self, other):
        spans = set()
        for hash_ in set(self._index) & set(other._index):
            spans |= self._index[hash_]
            spans |= other._index[hash_]
        return spans

    def unignored_tokens(self, file, tokens=None):
        if tokens is None:
            tokens = file.tokens()

        # Nothing to ignore
        if not self:
            return [tokens]

        # Create an index of file with same settings as self
        index = CompareIndex(k=self.k)
        index.include(file, tokens=tokens)

        # Figure out spans (regions) of the file to ignore
        # Note: these can overlap!
        ignored_spans = sorted(self.common_spans(index), key=lambda span: span.start)

        # Nothing to ignore
        if not ignored_spans:
            return [tokens]

        # Find relevant tokens (any token not completely in an ignored_span)
        relevant_token_lists = []
        relevant_tokens = []
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

    def fingerprint(self, file, tokens=None):
        if not tokens:
            tokens = file.tokens()
            if not tokens:
                return []

        hashes = self.hashes(tokens)

        starts = (tok.start for tok in tokens[:-self.k+1])
        ends = itertools.chain((tok.start for tok in tokens[self.k:]), (tokens[-1].end,))

        fingerprints = []

        # use all fingerprints instead of sampling
        for start, end, hash_ in zip(starts, ends, hashes):
            fingerprints.append((hash_, Span(file, start, end)))

        return fingerprints
