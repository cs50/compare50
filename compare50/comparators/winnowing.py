import copy
import collections
import math
import itertools

import compare50
import compare50.preprocessors as preprocessors
from compare50.data import FileMatch, SpanMatches, Span


class Winnowing(compare50.Comparator):
    def __init__(self, k, t):
        self.k = k
        self.t = t

    def cross_compare(self, submissions, archive_submissions, ignored_files):
        """"""
        submissions_index = Index(self.k, self.t)
        archive_index = Index(self.k, self.t)

        # Index all submissions
        for sub in submissions:
            for file in sub.files():
                submissions_index.add(file)

        # Index all archived submissions
        for sub in archive_submissions:
            for file in sub.files():
                archive_index.add(file)

        # Ignore all files from distro
        for file in ignored_files:
            submissions_index.remove(file)
            archive_index.remove(file)

        # Add submissions to archive (the Index we're going to compare against)
        archive_index |= submissions_index

        return submissions_index.compare(archive_index)

    def create_spans(self, file_a, file_b, ignored_files):
        a_index = Index(self.k, self.t, complete=True)
        b_index = Index(self.k, self.t, complete=True)

        a_index.add(file_a)
        b_index.add(file_b)

        for file in ignored_files:
            a_index.remove(file)
            b_index.remove(file)

        return SpanMatches()
        # TODO
        #return submissions_index.compare(archive_index)


class StripWhitespace(compare50.Pass):
    description = "Remove all whitespace, then run Winnowing with k=16, t=32."
    preprocessors = [preprocessors.strip_whitespace, preprocessors.by_character]
    comparator = Winnowing(k=16, t=32)


class StripAll(compare50.Pass):
    description = "Remove all whitespace, norm all comments/ids/strings, then run Winnowing with k=10, t=20."
    preprocessors = [preprocessors.strip_whitespace,
                     preprocessors.strip_comments,
                     preprocessors.normalize_identifiers,
                     preprocessors.normalize_string_literals]
    comparator = Winnowing(k=10, t=20)


class Index:
    def __init__(self, k, t, complete=False):
        self.k = k
        self.w = t - k + 1
        self._complete = complete
        self._index = collections.defaultdict(set)

    def add(self, file):
        for hash, span in self._fingerprint(file, complete=self._complete):
            self._index[hash].add(span)

    def remove(self, other):
        for hash, _ in self._fingerprint(file, complete=self._complete):
            self._index.pop(hash, None)

    def __ior__(self, other):
        for hash, spans in other._index.items():
            self._index[hash] |= spans
        return self

    def __or__(self, other):
        result = copy.deepcopy(self)
        result |= other
        return result

    def __sub__(self, other):
        result = copy.deepcopy(self)
        result -= other
        return result

    def __isub__(self, other):
        for hash, spans in other._index.items():
            self._index[hash] -= spans
        return self

    def compare(self, other):
        # validate other index
        if self.k != other.k:
            raise RuntimeError("comparison with different n-gram lengths")

        scores = collections.Counter()

        common_hashes = set(self._index.keys()) & set(other._index.keys())
        for hash in common_hashes:
            for span1, span2 in itertools.product(self._index[hash], other._index[hash]):
                if span1.file == span2.file:
                    continue
                # Normalize tuple order
                scores[tuple(sorted([span1.file, span2.file]))] += 1
        return [FileMatch(file1, file2, score) for (file1, file2), score in scores.items()]

    def _fingerprint(self, file, complete=False):
        tokens = list(file.tokens())

        kgrams = zip(*((tok.val for tok in tokens[i:]) for i in range(self.k)))
        hashes = (hash("".join(kgram)) for kgram in kgrams)

        starts = (tok.start for tok in tokens[:-self.k+1])
        ends = itertools.chain((tok.start for tok in tokens[self.k:]), (tokens[-1].end,))

        fingerprints = []
        if complete:
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
