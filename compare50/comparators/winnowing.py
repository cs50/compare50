import copy
import collections
import math
import numpy as np
import itertools

import concurrent.futures as futures

import compare50
import compare50.preprocessors as preprocessors
from compare50.data import FileMatch, SpanMatches, Span, File

class index_submission:
    def __init__(self, k, t):
        self.k = k
        self.t = t
    def __call__(self, submission):
        index = Index(self.k, self.t)
        for file in submission.files():
            index.include(file)
        return index

class index_file:
    def __init__(self, k, t):
        self.k = k
        self.t = t
    def __call__(self, file):
        index = Index(self.k, self.t)
        index.include(file)
        return index

class Winnowing(compare50.Comparator):
    def __init__(self, k, t):
        self.k = k
        self.t = t

    def cross_compare(self, submissions, archive_submissions, ignored_files):
        """"""
        submissions_index = Index(self.k, self.t)
        archive_index = Index(self.k, self.t)

        def iter_files(subs):
            for sub in subs:
                for file in sub.files():
                    yield file

        with futures.ProcessPoolExecutor() as executor:
            for index in executor.map(index_file(self.k, self.t), iter_files(submissions)):
                submissions_index.include_all(index)

            for index in executor.map(index_file(self.k, self.t), iter_files(archive_submissions)):
                archive_index.include_all(index)

            for index in executor.map(index_file(self.k, self.t), ignored_files):
                submissions_index.ignore_all(index)
                archive_index.ignore_all(index)



        # # Index all archived submissions
        # for sub in archive_submissions:
            # for file in sub.files():
                # archive_index.add(file)

        # Ignore all files from distro
        # for file in ignored_files:
            # submissions_index.remove(file)
            # archive_index.remove(file)

        # Add submissions to archive (the Index we're going to compare against)
        archive_index.include_all(submissions_index)

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
        self._max_id = 0
        self._id_to_file = {}

    def include(self, file):
        if file.id > self._max_id:
            self._max_id = file.id

        for hash, span in self._fingerprint(file):
            if self._complete:
                self._index[hash].add(span)
            else:
                self._index[hash].add(file.id)

    def ignore(self, other):
        for hash, _ in self._fingerprint(file):
            self._index.pop(hash, None)

    def include_all(self, other):
        for hash, spans in other._index.items():
            self._index[hash] |= spans
        self._max_id = max(self._max_id, other._max_id)
        return self

    def ignore_all(self, other):
        for hash in other._index():
            self._index.pop(hash, None)

    def compare(self, other):
        # Validate other index
        if self.k != other.k:
            raise RuntimeError("comparison with different n-gram lengths")

        # Keep a self.max_file_id by other.max_file_id matrix for counting score
        scores = np.zeros((self._max_id + 1, other._max_id + 1))

        # Find common fingerprints (hashes)
        common_hashes = set(self._index.keys()) & set(other._index.keys())
        for hash_ in common_hashes:
            # All file_ids associated with fingerprint in self
            index_1 = self._index[hash_]
            # All file_ids associated with fingerprint in other
            index_2 = other._index[hash_]
            if index_1 and index_2:
                # Create the product of all file_ids from self and other
                # https://stackoverflow.com/questions/28684492/numpy-equivalent-of-itertools-product
                index = np.array(np.meshgrid(list(index_1), list(index_2))).T.reshape(-1, 2)
                # index = index[index[:,0] < index[:,1]]

                # Add 1 to all combo's (the product) of file_ids from self and other
                scores[index[:,0], index[:,1]] += 1

        # Return only those FileMatches with a score > 0 from different submissions

        return [FileMatch(File.get(id1), File.get(id2), scores[id1][id2])
                for id1, id2 in zip(*np.where(np.triu(scores, 1) > 0))]

    def _fingerprint(self, file):
        tokens = list(file.tokens())

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
