import collections
import math
import itertools
import compare50.config as config
import compare50.preprocessors as preprocessors
from compare50.data import Compare50Comparator, FileMatch, SpanMatches, Span


class StripWhitespace(config.Compare50Config):
    def id(self):
        return "win_strip_ws"

    def description(self):
        return "Remove all whitespace, then run Winnowing with k=16, t=32."

    def preprocessors(self):
        return [preprocessors.strip_whitespace, preprocessors.by_character]

    def comparator(self):
        return Comparator(k=16, t=32)
config.register(StripWhitespace())


class StripAll(config.Compare50Config):
    def id(self):
        return "win_strip_all"

    def description(self):
        return "Remove all whitespace, norm all comments/ids/strings, then run Winnowing with k=10, t=20."

    def preprocessors(self):
        return [preprocessors.strip_whitespace,
                preprocessors.strip_comments,
                preprocessors.normalize_identifiers,
                preprocessors.normalize_string_literals]

    def comparator(self):
        return Comparator(k=10, t=20)
config.register(StripAll())


class Comparator(Compare50Comparator):
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
                submissions_index.include(Index(self.k, self.t, file=file))

        # Index all archived submissions
        for sub in archive_submissions:
            for file in sub.files():
                archive_index.include(Index(self.k, self.t, file=file))

        # Ignore all files from distro
        for file in ignored_files:
            submissions_index.ignore(file)
            archive_index.ignore(file)

        # Add submissions to archive (the Index we're going to compare against)
        archive_index.include(submissions_index)

        return submissions_index.cross_compare(archive_index)
        #return [FileMatch(list(submissions[0].files())[0], list(submissions[1].files())[0], 10), \
                    #FileMatch(list(submissions[1].files())[0], list(submissions[2].files())[0], 20)]

    def create_spans(self, file_a, file_b, ignored_files):
        # TODO
        pass


class Index:
    def __init__(self, k, t, file=None):
        self.k = k
        self.w = t - k + 1
        self._index = collections.defaultdict(set)
        if file is not None:
            for hash, span in self._fingerprint(file):
                self._index[hash].add(span)

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

        common_hashes = set(self._index.keys()) & set(other._index.keys())
        for hash in common_hashes:
            # map submissions to spans for both indices
            for span1, span2 in itertools.product(self._index[hash], other._index[hash]):
                if span1.file == span2.file:
                    continue
                # Normalize tuple order
                scores[tuple(sorted([span1.file, span2.file]))] += 1
        return [FileMatch(file1, file2, score) for (file1, file2), score in scores.items()]

    @staticmethod
    def create_spans():
        pass


    def _fingerprint(self, file, complete=False):
        tokens = list(file.tokens())

        kgrams = zip(*((tok.val for tok in tokens[i:]) for i in range(self.k)))
        hashes = (hash("".join(kgram)) for kgram in kgrams)

        if complete:
            starts = (tok.start for tok in tokens[self.k:])
            ends = itertools.chain((tok.start for tok in tokens[self.k:]), (tokens[-1].end,))
            # use all fingerprints instead of sampling
            for start, end, hash_ in zip(starts, ends, hashes):
                yield hash_, Span(file, start, end)
        else:
            # circular buffer holding window
            buf = [(math.inf, Span(None, 0, 0))] * self.w
            # index of minimum hash in buffer
            indices = [tok.start for tok in tokens]
            indices.append(tokens[-1].end)

            min_idx = 0
            for (hash_, idx) in zip(hashes, itertools.cycle(range(self.w))):
                start = indices[idx]
                end = indices[idx + self.k]

                buf[idx] = hash_, Span(file, start, end)
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
