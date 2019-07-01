import abc
import collections
import itertools
import math
import sys

import attr
import numpy as np


from .. import _api, Comparison, Comparator, Submission, Span, Score


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
        """Number of matching k-grams."""
        def files(subs):
            return [f for sub in subs for f in sub]

        submission_index = ScoreIndex(self.k, self.t)
        archive_index = ScoreIndex(self.k, self.t)
        ignored_index = ScoreIndex(self.k, self.t)

        submission_files = files(submissions)
        archive_files = files(archive_submissions)

        bar = _api.get_progress_bar()
        bar.reset(total=math.ceil((len(submission_files) + len(archive_files) + len(ignored_files)) / 0.9))
        frequency_map = collections.Counter()
        with _api.Executor() as executor:
            # Subs and archive subs
            for index, files in ((submission_index, submission_files), (archive_index, archive_files)):
                for idx in executor.map(self._index_file(ScoreIndex, (self.k, self.t)), files):
                    for hash_ in idx.keys():
                        frequency_map[hash_] += 1
                    index.include_all(idx)
                    bar.update()
            # Ignored files
            for idx in executor.map(self._index_file(ScoreIndex, (self.k, self.t)), ignored_files):
                index.include_all(idx)
                bar.update()


        submission_index.ignore_all(ignored_index)
        archive_index.ignore_all(ignored_index)

        # Add submissions to archive (the Index we're going to compare against)
        archive_index.include_all(submission_index)

        N = len(submissions) + len(archive_submissions)
        return submission_index.compare(archive_index, score=lambda h: 1 + math.log(N / (1 + frequency_map[h])))

    def compare(self, scores, ignored_files):

        bar = _api.get_progress_bar()
        bar.reset(total=len(scores) if scores else 1)
        if not scores:
            return []

        # Create index of ignored_files
        ignored_index = CompareIndex(self.k)
        for ignored_file in ignored_files:
            ignored_index.include(ignored_file)

        # Find all unique submissions
        subs = set()
        for s in scores:
            subs.add(s.sub_a)
            subs.add(s.sub_b)

        # TODO: Rename me
        # Basically a named tuple of information we need to keep around for each file
        @attr.s(slots=True)
        class FileCache:
            # List of tokens (and their corresponding indices) that can be matched.
            # Name is slightly misleading since it is a list of (token, index) pairs
            unignored_tokens = attr.ib(factory=list)
            ignored_spans = attr.ib(factory=list)


        file_cache = {}
        for sub in subs:
            for file in sub:
                file_tokens = file.tokens()
                cache = FileCache()

                # Get list of unignored tokens
                token_lists = ignored_index.unignored_tokens(file, tokens=file_tokens)
                # Index each stretch of unignored tokens, index and add to the cache
                for token_list in token_lists:
                    index = CompareIndex(self.k)
                    index.include(file, tokens=token_list)
                    cache.unignored_tokens.append((token_list, index))

                cache.ignored_spans = _api.missing_spans(file,
                                                         original_tokens=file_tokens,
                                                         processed_tokens=list(itertools.chain.from_iterable(token_lists)))
                file_cache[file] = cache



        comparisons = []
        for score in scores:
            ignored_spans = set()
            span_matches = []

            # We already have the ignored spans for every file cached, so we just need to get the list
            # for each file in this submission pair.
            for file in itertools.chain(score.sub_a.files, score.sub_b.files):
                ignored_spans.update(file_cache[file].ignored_spans)

            # Compare each pair of files in the submission pair
            for file_a, file_b in itertools.product(score.sub_a.files, score.sub_b.files):
                cache_a = file_cache[file_a]
                cache_b = file_cache[file_b]
                # For each pair of unignored regions in the file pair, find the matching spans
                # (by comparing their indices) and expand them as much as possible
                for (tokens_a, index_a), (tokens_b, index_b) in itertools.product(cache_a.unignored_tokens, cache_b.unignored_tokens):
                    span_matches += _api.expand(index_a.compare(index_b), tokens_a, tokens_b)

            comparisons.append(Comparison(score.sub_a, score.sub_b, span_matches, list(ignored_spans)))
            bar.update()

        return comparisons


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
    """Abstract base class for a map between (hashed) fingerprints (k-grams) and the Spans
    they come from.
    :param k: the size of the fingerprints, or equivalently the "noise threshold", the \
              number of tokens that must be identical between two files for us to consider
              it a match.
    """
    def __init__(self, k):
        self.k = k
        self._index = collections.defaultdict(set)

    def keys(self):
        return self._index.keys()

    def values(self):
        return self._index.values()

    def include(self, file, tokens=None):
        """Fingerprint a file and add it too the index."""
        for hash, val in self.fingerprint(file, tokens):
            self._index[hash].add(val)

    def include_all(self, other):
        """Add all fingerprints from another index into this one."""
        for hash, vals in other._index.items():
            self._index[hash] |= vals
        return self

    def ignore_all(self, other):
        """Remove all fingerprints in another index from this one."""
        for hash in other._index:
            self._index.pop(hash, None)

    def kgrams(self, iterable):
        """
        Create an iterator over all contiguous sequences of k items (kgrams) from
        ``iterable``.
        """
        iters = itertools.tee(iterable, self.k)
        for i, it in enumerate(iters):
            next(itertools.islice(it, i, i), None)
        return zip(*iters)

    def hashes(self, tokens):
        """Hash each contiguous sequence of k tokens in ``tokens``."""
        return (hash("".join(kgram)) for kgram in self.kgrams(t.val for t in tokens))

    @abc.abstractmethod
    def compare(self, other):
        pass

    @abc.abstractmethod
    def fingerprint(self, file, tokens=None):
        pass

    def __bool__(self):
        return bool(self._index)


class ScoreIndex(Index):
    def __init__(self, k, t):
        super().__init__(k)
        self.w = t - k + 1
        self._max_id = 0

    def include(self, file, tokens=None):
        super().include(file, tokens)
        self._max_id = max(self._max_id, file.submission.id)

    def include_all(self, other):
        super().include_all(other)
        self._max_id = max(self._max_id, other._max_id)

    def compare(self, other, score=lambda _: 1):
        # Keep a self.max_file_id by other.max_file_id matrix for counting score
        scores = np.zeros((self._max_id + 1, other._max_id + 1), dtype=np.float64)

        # Find common fingerprints (hashes)
        common_hashes = set(self._index) & set(other._index)

        bar = _api.get_progress_bar()
        try:
            update_amount = (bar.total - bar.n - 1) / len(common_hashes)
        except ZeroDivisionError:
            pass

        for hash_ in common_hashes:
            bar.update(update_amount)

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
                scores[index[:, 0], index[:, 1]] += score(hash_)

        # Return only those Scores with a score > 0 from different submissions
        return [Score(Submission.get(id1), Submission.get(id2), scores[id1][id2])
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
        matches = []

        # Find common fingerprints (hashes)
        common_hashes = set(self._index) & set(other._index)
        for hash_ in common_hashes:
            # All spans associated with fingerprint in self
            spans_a = self._index[hash_]
            # All spans associated with fingerprint in other
            spans_b = other._index[hash_]
            matches.extend((span_a, span_b)
                           for span_a, span_b in itertools.product(spans_a, spans_b))

        return matches

    def unignored_tokens(self, file, tokens=None):
        if tokens is None:
            tokens = file.tokens()

        # Nothing to ignore
        if not self:
            return [tokens]

        # Create an index of file with same settings as self
        file_index = CompareIndex(k=self.k)
        file_index.include(file, tokens=tokens)

        # Figure out spans (regions) of the file to ignore
        # Note: these can overlap!
        ignored_spans = []
        for hash, spans in file_index._index.items():
            if hash in self._index:
                ignored_spans.extend(spans)

        # Nothing to ignore
        if not ignored_spans:
            return [tokens]

        # Find relevant tokens (any token not completely in an ignored_span)
        relevant_token_lists = []
        relevant_tokens = []
        span_iter = iter(sorted(ignored_spans, key=lambda span: span.start))
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
