import hashlib
import math


class WinnowingIndex(object):
    def __init__(self, k, fingerprints):
        self.k = k
        self.fingerprints = fingerprints

    def __repr__(self):
        return "\n".join(str(f) for f in self.fingerprints)

    def compare(self, other):
        if not isinstance(other, WinnowingIndex):
            raise Exception("comparison between different index types")
        if self.k != other.k:
            raise Exception("comparison with different n-gram lengths")
        # TODO: comparison with other winnowing index


class Winnowing(object):
    def __init__(self, k, t):
        self.k = k
        self.w = t - k + 1

    def create_index(self, text):
        """
        Given a ProcessedText, return a set of (hash, position) fingerprints
        """
        doc_indices, chars = zip(*text.chars())
        hashes = [self._compute_hash(chars[i:i+self.k])
                  for i in range(len(chars) - self.k + 1)]

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
                fingerprints.append((buf[min_idx], doc_indices[i]))
            else:
                # compare new hash to old min (robust winnowing)
                if buf[idx] < buf[min_idx]:
                    min_idx = idx
                    fingerprints.append((buf[min_idx], doc_indices[i]))

        return WinnowingIndex(self.k, fingerprints)

    def _compute_hash(self, s):
        """Given a string or list of strings, generate a hash."""
        hasher = hashlib.sha256()
        for t in s:
            hasher.update(t.encode("utf-8"))
        return int(hasher.hexdigest()[:16], 16)
