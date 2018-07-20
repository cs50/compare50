import abc
import collections
import math
import itertools
from data import Span, MatchResult

class FileIndex(metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def __init__(self, file=None, **kwargs):
        pass

    @abc.abstractmethod
    def include(self, other):
        pass

    @abc.abstractmethod
    def ignore(self, file):
        pass

    @abc.abstractmethod
    def cross_compare(self, other):
        pass

    @staticmethod
    @abc.abstractmethod
    def create_spans(file1, file2):
        pass


class WinnowingIndex(FileIndex):
    def __init__(self, k, w, file=None):
        self.k = k
        self.w = t - k + 1
        self._index = collections.defaultdict(set, self._fingerprint(file))

    def include(self, other):
        for hash, spans in other._index.items():
            self._index[hash] |= spans

    def ignore(self, other):
        for hash in other._index:
            self._index.pop(hash, None)

    def cross_compare(self, other):
        # validate other index
        if self.k != other.k:
            raise RuntimeError("comparison with different n-gram lengths")

        # map submission pairs to scores
        scores = collections.Counter()

        common_hashes = set(self.index.keys()) & set(other.index.keys())
        for hash in common_hashes:
            # map submissions to spans for both indices
            for span1, span2 in itertools.product(self.index[hash], other.index[hash]):
                if span1.file == span2.file:
                    continue
                # Normalize tuple order
                scores[tuple(sorted(span1.file, span2.file))] += 1
        return [FileMatch(file1, file2, score) for (file1, file2), score in scores.items()]

    @staticmethod
    def create_spans():
        pass


    def _fingerprint(self, file, complete=False):
        tokens = list(file.tokens)

        kgrams = zip(*((tok.val for tok in tokens[i:]) for i in range(self.k)))
        hashes = (hash("".join(kgram)) for kgram in kgrams)

        if complete:
            starts = (tok.start for tok in tokens[self.k:])
            ends = itertools.chain((tok.start for tok in tokens[self.k:]), (tokens[-1].end,))
            # use all fingerprints instead of sampling
            for start, end, hash in zip(starts, ends, hashes):
                yield hash, Span(file, start, end)
        else:
            # circular buffer holding window
            buf = [(Span(None, 0, 0), math.inf)] * self.w
            # index of minimum hash in buffer

            min_idx = 0
            for (start, end, hash, idx) in zip(starts, ends, hashes, itertools.cycle(range(self.w))):
                buf[idx] = hashes[i], Span(file, indices[i], indices[i+self.k])
                if min_idx == idx:
                    # old min not in window, search left for new min
                    for j in range(1, self.w):
                        search_idx = (idx - j) % self.w
                        if buf[search_idx][0] < buf[min_idx][0]:
                            min_idx = search_idx
                    yield buf[min_idx]
                else:
                    # compare new hash to old min (robust winnowing)
                    if buf[idx][0] < buf[min_idx][0]:
                        min_idx = idx
                        yield buf[min_idx]
