import math
import heapq
from data import Span, MatchResult

class Index:
    """A reverse index mapping hashes to (id, span) pairs"""
    def __init__(self, k, fingerprints, sub_id):
        self.k = k
        self.index = dict()
        for span, hash in fingerprints:
            self._insert(hash, sub_id, span)

    def _insert(self, h, sub_id, span):
        self.index.setdefault(h, set()).add((sub_id, span))

    def __iadd__(self, other):
        if other.k != self.k:
            raise Exception("Combining indices of different n-gram lengths")
        for h, entry in other.index.items():
            for sub_id, span in entry:
                self._insert(h, sub_id, span)
        return self

    def __add__(self, other):
        result = Index.empty(self.k)
        result += self
        result += other
        return result

    def __isub__(self, other):
        for h in other.index.keys():
            self.index.pop(h, None)
        return self

    def __sub__(self, other):
        result = Index.empty(self.k)
        result += self
        result -= other
        return result

    def compare(self, other, n=50):
        # validate other index
        if not isinstance(other, Index):
            raise Exception("comparison between different index types")
        if self.k != other.k:
            raise Exception("comparison with different n-gram lengths")

        # map submission pairs to maps of hashes to list of spans
        results = {}

        common_hashes = set(self.index.keys()) & set(other.index.keys())
        for hash in common_hashes:
            # map submissions to spans for both indices
            local_spans = {}
            for sub_id, span in self.index[hash]:
                local_spans.setdefault(sub_id, set()).add(span)
            other_spans = {}
            for sub_id, span in other.index[hash]:
                other_spans.setdefault(sub_id, set()).add(span)

            # record submissions that share the current hash
            for sub_id1, spans1 in local_spans.items():
                for sub_id2, spans2 in other_spans.items():
                    # XXX: depends on "submission" being local and
                    # "archive" being other, and also on all
                    # "submission" IDs being less than all "archive"
                    # ids. The non-hack way is to normalize order of
                    # the sub_id pair (into fresh variables) and
                    # continue only if they are equal or already
                    # processed. Reduces `compare` time by 37% with
                    # n=640.
                    if sub_id2 <= sub_id1:
                        continue

                    # update results
                    pair = (sub_id1, sub_id2)
                    entry = results.setdefault(pair, dict())
                    entry = entry.setdefault(hash, set())
                    entry |= spans1 | spans2

        def score(hashes):
            return sum(len(spans) for spans in hashes.values())

        top_matches = heapq.nlargest(n, results.items(), lambda x: score(x[1]))
        returned = [MatchResult(a, b, score(hashes), hashes)
                    for (a, b), hashes in top_matches]
        return returned

    @staticmethod
    def empty(k):
        return Index(k, [], None)


class Winnowing:
    def __init__(self, k, t):
        self.k = k
        self.w = t - k + 1

    def empty_index(self):
        return Index.empty(self.k)

    def index(self, file, tokens, complete=False):
        if not tokens:
            return self.empty_index()

        indices = [tok.start for tok in tokens]
        indices.append(tokens[-1].stop)
        items = [tok.val for tok in tokens]

        # hash all k-grams
        hashes = [self._hash((items[i:i+self.k]))
                  for i in range(len(items) - self.k + 1)]

        if complete:
            # use all fingerprints instead of sampling
            fingerprints = [(Span(file, indices[i], indices[i+self.k]),
                             hashes[i])
                            for i in range(len(hashes))]
        else:
            # circular buffer holding window
            buf = [(Span(None, 0, 0), math.inf)] * self.w
            # index of minimum hash in buffer
            min_idx = 0
            fingerprints = []
            for i in range(len(hashes)):
                # index in buffer
                idx = i % self.w
                buf[idx] = (Span(file, indices[i], indices[i+self.k]), hashes[i])
                if min_idx == idx:
                    # old min not in window, search left for new min
                    for j in range(1, self.w):
                        search_idx = (idx - j) % self.w
                        if buf[search_idx][1] < buf[min_idx][1]:
                            min_idx = search_idx
                    fingerprints.append(buf[min_idx])
                else:
                    # compare new hash to old min (robust winnowing)
                    if buf[idx][1] < buf[min_idx][1]:
                        min_idx = idx
                        fingerprints.append(buf[min_idx])

        return Index(self.k, fingerprints, file.submission_id)

    def _hash(self, s):
        return hash("".join(s))
