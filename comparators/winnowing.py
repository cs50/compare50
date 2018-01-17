import hashlib
import math
import os

from util import Span, Match


class WinnowingIndex(object):
    """A reverse index mapping hashes to (id, span) pairs"""
    def __init__(self, k, fingerprints, submission_id):
        self.k = k
        self.index = dict()
        for h, span in fingerprints:
            self._insert(h, submission_id, span)

    def _insert(self, h, submission_id, span):
        self.index.setdefault(h, set()).add((submission_id, span))

    def __iadd__(self, other):
        if other.k != self.k:
            raise Exception("Combining indices of different n-gram lengths")
        for h, entry in other.index.items():
            for id, span in entry:
                self._insert(h, id, span)
        return self

    def __add__(self, other):
        result = WinnowingIndex(self.k, [], None)
        result += self
        result += other
        return result

    def __isub__(self, other):
        for h in other.index.keys():
            self.index.pop(h, None)
        return self

    def __sub__(self, other):
        result = WinnowingIndex(self.k, [], None)
        result += self
        result -= other
        return result

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

    def create_index(self, file, preprocessor):
        """
        Given a preprocessor and file, return a set of (hash, position)
        fingerprints
        """
        text = preprocessor.process(file)
        submission_id = os.path.dirname(file)
        if self.by_span:
            indices = [span.start for span in text.spans]
            items = [span.text for span in text.spans]
        else:
            indices, items = zip(*text.chars())
        hashes = [self._compute_hash(items[i:i+self.k])
                  for i in range(len(items) - self.k + 1)]
        # circular buffer holding window
        buf = [(math.inf, Span(0, 0, None))] * self.w
        # index of minimum hash in buffer
        min_idx = 0
        fingerprints = []
        for i in range(len(hashes)):
            # index in buffer
            idx = i % self.w
            span_end = indices[i+self.k-1] + len(items[i+self.k-1])
            buf[idx] = (hashes[i], Span(indices[i], span_end, file))
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
        return WinnowingIndex(self.k, fingerprints, submission_id)

    def _compute_hash(self, s):
        """Given a string or list of strings, generate a hash."""
        hasher = hashlib.sha256()
        for t in s:
            hasher.update(t.encode("utf-8"))
        return int(hasher.hexdigest()[:16], 16)
