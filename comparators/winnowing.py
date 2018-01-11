import hashlib
import math

from util import Span, Match


class WinnowingIndex(object):
    """A reverse index mapping hashes to (id, span) pairs"""
    def __init__(self, k, fingerprints, id):
        self.k = k
        self.index = dict()
        for h, span in fingerprints:
            self._insert(h, id, span)

    def _insert(self, h, id, span):
        self.index.setdefault(h, set()).add((id, span))

    def extend(self, other):
        for h, entry in other.index.items():
            for id, span in entry:
                self._insert(h, id, span)

    def remove(self, other):
        for h in other.index.keys():
            self.index.pop(h)

    def compare(self, other):
        # validate other index
        if not isinstance(other, WinnowingIndex):
            raise Exception("comparison between different index types")
        if self.k != other.k:
            raise Exception("comparison with different n-gram lengths")

        # map id pairs to pairs of lists of spans
        matches = {}
        # map id pairs to the number of distinct shared hashes
        # TODO: weight hashes by frequency across all files
        weights = {}
        common_keys = set(self.index.keys()) & set(other.index.keys())
        for key in common_keys:
            local_spans = {}
            for id, span in self.index[key]:
                local_spans.setdefault(id, []).append(span)
            other_spans = {}
            for id, span in other.index[key]:
                other_spans.setdefault(id, []).append(span)
            for id1, spans1 in local_spans.items():
                for id2, spans2 in other_spans.items():
                    if id1 != id2 and (id2, id1) not in matches:
                        pair = (id1, id2)
                        matches_entry = matches.setdefault(pair, ([], []))
                        matches_entry[0].extend(spans1)
                        matches_entry[1].extend(spans2)
                        weights[pair] = weights.setdefault(pair, 0) + 1

        # coalesce spans and create match objects
        results = []
        for (id1, id2), (spans1, spans2) in matches.items():
            weight = weights[(id1, id2)]
            spans1 = Span.coalesce(spans1)
            spans2 = Span.coalesce(spans2)
            results.append(Match(weight, id1, spans1, id2, spans2))

        return Match.ordered(results)


class Winnowing(object):
    def __init__(self, k, t, by_span=False):
        self.k = k
        self.w = t - k + 1
        self.by_span = by_span

    def create_index(self, id, text):
        """
        Given a ProcessedText, return a set of (hash, position) fingerprints
        """
        if self.by_span:
            indices = [span.start for span in text.spans]
            items = [span.text for span in text.spans]
        else:
            indices, items = zip(*text.chars())
        hashes = [self._compute_hash(items[i:i+self.k])
                  for i in range(len(items) - self.k + 1)]

        # circular buffer holding window
        buf = [math.inf] * self.w
        # index of minimum hash in buffer
        min_idx = 0
        fingerprints = []
        for i in range(len(hashes)):
            # index in buffer
            idx = i % self.w
            buf[idx] = hashes[i]
            if min_idx == idx:
                # old min not in window, search left for new min
                for j in range(1, self.w):
                    search_idx = (idx - j) % self.w
                    if buf[search_idx] < buf[min_idx]:
                        min_idx = search_idx
                fingerprints.append(
                    (buf[min_idx], Span(indices[i], indices[i+self.k-1]+1))
                )
            else:
                # compare new hash to old min (robust winnowing)
                if buf[idx] < buf[min_idx]:
                    min_idx = idx
                    fingerprints.append(
                        (buf[min_idx], Span(indices[i], indices[i+self.k-1]+1))
                    )

        return WinnowingIndex(self.k, fingerprints, id)

    def _compute_hash(self, s):
        """Given a string or list of strings, generate a hash."""
        hasher = hashlib.sha256()
        for t in s:
            hasher.update(t.encode("utf-8"))
        return int(hasher.hexdigest()[:16], 16)
