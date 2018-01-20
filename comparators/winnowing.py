import math
from util import Span


class WinnowingIndex(object):
    """A reverse index mapping hashes to (id, span) pairs"""
    def __init__(self, k, fingerprints, sub_id):
        self.k = k
        self.index = dict()
        for h, span in fingerprints:
            self._insert(h, sub_id, span)

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
        result = WinnowingIndex.empty(self.k)
        result += self
        result += other
        return result

    def __isub__(self, other):
        for h in other.index.keys():
            self.index.pop(h, None)
        return self

    def __sub__(self, other):
        result = WinnowingIndex.empty(self.k)
        result += self
        result -= other
        return result

    def compare(self, other):
        # validate other index
        if not isinstance(other, WinnowingIndex):
            raise Exception("comparison between different index types")
        if self.k != other.k:
            raise Exception("comparison with different n-gram lengths")

        # map id pairs to lists of pairs of sets of spans
        matches = {}
        # map id pairs to the number of distinct shared hashes
        # TODO: weight by min file length
        scores = {}
        common_hashes = set(self.index.keys()) & set(other.index.keys())
        for h in common_hashes:
            # record pairs seen to prevent double counting
            processed = set()

            # map submissions to spans for both indices
            local_spans = {}
            for sub_id, span in self.index[h]:
                local_spans.setdefault(sub_id, set()).add(span)
            other_spans = {}
            for sub_id, span in other.index[h]:
                other_spans.setdefault(sub_id, set()).add(span)

            # record submissions that share the current hash
            for sub_id1, spans1 in local_spans.items():
                for sub_id2, spans2 in other_spans.items():
                    # normalize order of submission pair
                    if sub_id1 <= sub_id1:
                        n_id1, n_id2 = sub_id1, sub_id2
                        n_spans1, n_spans2 = spans1, spans2
                    if sub_id2 < sub_id1:
                        n_id1, n_id2 = sub_id2, sub_id1
                        n_spans1, n_spans2 = spans2, spans1

                    # ignore repeats and matches with self
                    pair = (n_id1, n_id2)
                    if n_id1 == n_id2 or pair in processed:
                        continue

                    # update results
                    processed.add(pair)
                    matches.setdefault(pair, []).append((n_spans1, n_spans2))
                    scores[pair] = scores.setdefault(pair, 0) + 1

        return [(pair, scores[pair], matches[pair]) for pair in matches.keys()]

    @staticmethod
    def empty(k):
        return WinnowingIndex(k, [], None)


class Winnowing(object):
    def __init__(self, k, t, by_span=False):
        self.k = k
        self.w = t - k + 1
        self.by_span = by_span

    def empty_index(self):
        return WinnowingIndex.empty(self.k)

    def create_index(self, file, text, sub_id):
        """
        Given a file name, preprocessed text, and submission id, return a set of
        (hash, position) fingerprints
        """
        if self.by_span:
            indices = [span.start for _, span in text.spans]
            indices.append(text.spans[-1][1].stop)
            items = [text for text, _ in text.spans]
        else:
            indices, items = map(list, zip(*text.chars()))
            indices.append(indices[-1] + 1)

        hashes = [self._hash((items[i:i+self.k]))
                  for i in range(len(items) - self.k + 1)]

        # circular buffer holding window
        buf = [(math.inf, Span(0, 0, None))] * self.w
        # index of minimum hash in buffer
        min_idx = 0
        fingerprints = []
        for i in range(len(hashes)):
            # index in buffer
            idx = i % self.w
            buf[idx] = (hashes[i], Span(indices[i], indices[i+self.k], file))
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
        return WinnowingIndex(self.k, fingerprints, sub_id)

    def _hash(self, s):
        return hash("".join(s))
