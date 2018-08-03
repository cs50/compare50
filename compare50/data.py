import abc
from collections.abc import Mapping, Sequence
import os
import pathlib

import attr
import pygments
import pygments.lexers



class Comparator(metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def cross_compare(self, submissions, archive_submissions, ignored_files):
        pass

    @abc.abstractmethod
    def create_spans(self, matches, ignored_files):
        pass


class IdStore(Mapping):
    def __init__(self, key=lambda obj: obj):
        self.objects = []
        self._key = key
        self._ids = {}

    def __getitem__(self, obj):
        key = self._key(obj)
        if key not in self._ids:
            self._ids[key] = len(self.objects)
            self.objects.append(obj)
        return self._ids[key]

    def __iter__(self):
        return iter(self.objects.values())

    def __len__(self):
        return len(self.objects)

@attr.s(slots=True, frozen=True, hash=True)
class Submission:
    _store = IdStore(key=lambda sub: (sub.path, sub.files))

    path = attr.ib(converter=pathlib.Path, hash=False, cmp=False)
    files = attr.ib(hash=False, cmp=False)
    preprocessor = attr.ib(default=lambda tokens: tokens, hash=False, cmp=False, repr=False)
    id = attr.ib(init=False)

    def __attrs_post_init__(self):
        object.__setattr__(self, "files", tuple([File(pathlib.Path(path).name, self) for path in self.files]))
        object.__setattr__(self, "id", Submission._store[self])

    @classmethod
    def get(cls, id):
        return cls._store.objects[id]

@attr.s(slots=True, frozen=True, hash=True)
class File:
    _lexer_cache = {}
    _store = IdStore(key=lambda file: file.path)

    name = attr.ib(converter=pathlib.Path, cmp=False, hash=False)
    submission = attr.ib(cmp=False, hash=False)
    id = attr.ib(default=attr.Factory(lambda self: self._store[self], takes_self=True), init=False)

    @property
    def path(self):
        return self.submission.path / self.name

    def read(self, size=-1):
        with open(self.path) as f:
            return f.read(size)

    def tokens(self):
        return self.submission.preprocessor(self._tokenize())

    def lexer(self):
        ext = self.name.suffix
        try:
            return self._lexer_cache[ext]
        except KeyError:
            pass

        # get lexer for this file type
        try:
            lexer = pygments.lexers.get_lexer_for_filename(self.name.name)
            self._lexer_cache[ext] = lexer
            return lexer
        except pygments.util.ClassNotFound:
            try:
                return pygments.lexers.guess_lexer(self.read())
            except pygments.util.ClassNotFound:
                return pygments.lexers.special.TextLexer()

    @classmethod
    def get(cls, id):
        return cls._store.objects[id]

    def _tokenize(self):
        text = self.read()
        tokens = self.lexer().get_tokens_unprocessed(text)

        prevToken = None
        for token in tokens:
            if prevToken:
                yield Token(start=prevToken[0], end=token[0],
                            type=prevToken[1], val=prevToken[2])

            prevToken = token

        if prevToken:
            yield Token(start=prevToken[0], end=len(text),
                        type=prevToken[1], val=prevToken[2])


@attr.s(slots=True, frozen=True, hash=True, repr=False)
class Span:
    """Represents a range of characters in a particular file.

    file - the ID of the File containing the span
    start - the character index of the first character in the span
    end - the character index one past the end of the span
    """
    file = attr.ib()
    start = attr.ib()
    end = attr.ib()

    def __repr__(self):
        return "Span({} {}:{})".format(self.file.path.relative_to(self.file.submission.path.parent), self.start, self.end)

    def _raw_contents(self):
        return self.file.read()[self.start:self.end]


@attr.s(slots=True, frozen=True, hash=True)
class FileMatch:
    file_a = attr.ib()
    file_b = attr.ib()
    score = attr.ib()


@attr.s(slots=True)
class SpanMatches:
    _matches = attr.ib(default=attr.Factory(list), converter=list)

    def add(self, span_a, span_b):
        if span_a.file.id < span_b.file.id:
            span_match = (span_a, span_b)
        else:
            span_match = (span_b, span_a)
        self._matches.append(span_match)

    @property
    def file_a(self):
        return self._matches[0][0].file

    @property
    def file_b(self):
        return self._matches[0][1].file

    def __iter__(self):
        return iter(self._matches)

    def expand(self, tokens_a=None, tokens_b=None):
        """
        Expand all spans in this SpanMatches.
        returns a new instance of SpanMatches with maximally extended spans.
        """
        if not self._matches:
            return self

        expanded_span_pairs = set()

        tokens_a = SortedList.from_sorted(tokens_a if tokens_a else self.file_a.tokens(),
                                          key=lambda tok: tok.start)
        tokens_b = SortedList.from_sorted(tokens_b if tokens_b else self.file_b.tokens(),
                                          key=lambda tok: tok.start)

        for span_a, span_b in self._matches:
            # Expand left
            start_a = tokens_a.bisect_key_right(span_a.start) - 2
            start_b = tokens_b.bisect_key_right(span_b.start) - 2
            while min(start_a, start_b) >= 0 and tokens_a[start_a] == tokens_b[start_b]:
                start_a -= 1
                start_b -= 1
            start_a += 1
            start_b += 1

            # Expand right
            end_a = tokens_a.bisect_key_right(span_a.end) - 2
            end_b = tokens_b.bisect_key_right(span_b.end) - 2
            try:
                while tokens_a[end_a] == tokens_b[end_b]:
                    end_a += 1
                    end_b += 1
            except IndexError:
                pass
            end_a -= 1
            end_b -= 1

            new_span_a = Span(span_a.file, tokens_a[start_a].start, tokens_a[end_a].end)
            new_span_b = Span(span_b.file, tokens_b[start_b].start, tokens_b[end_b].end)

            # Add new spans
            expanded_span_pairs.add((new_span_a, new_span_b))

        self._matches = list(expanded_span_pairs)
        return self

    def __iter__(self):
        return iter(self._matches)


@attr.s(slots=True, frozen=True, hash=True)
class SubmissionMatch:
    sub_a = attr.ib()
    sub_b = attr.ib()
    file_matches = attr.ib()
    score = attr.ib(init=False, default=attr.Factory(lambda self: sum(f.score for f in self.file_matches), takes_self=True))


def _sorted_subs(group):
    sub = None
    for span in group.spans:
        if not sub:
            sub = span.file.submission
        elif sub < span.file.submission:
            return (sub, span.file.submission)
        elif sub > span.file.submission:
            return (span.file.submission, sub)

@attr.s(slots=True, frozen=True, hash=True)
class Group:
    spans = attr.ib(converter=frozenset)
    _subs = attr.ib(init=False, default=attr.Factory(_sorted_subs, takes_self=True))

    @property
    def sub_a(self):
        return self._subs[0]

    @property
    def sub_b(self):
        return self._subs[1]

    @property
    def sub_a_files(self):
        return {span.file for span in self.spans if span.file.submission == self.sub_a}

    @property
    def sub_b_files(self):
        return {span.file for span in self.spans if span.file.submission == self.sub_b}


@attr.s(slots=True, cmp=True)
class Token:
    """A result of the lexical analysis of a file. Preprocessors operate
    on Token streams.

    start - the character index of the beginning of the token
    end - the character index one past the end of the token
    type - the Pygments token type
    val - the string contents of the token
    """
    start = attr.ib(cmp=False)
    end = attr.ib(cmp=False)
    type = attr.ib()
    val = attr.ib()

    def __eq__(self, other):
        """Note that there is no sanity checking, sacrificed for performance."""
        return self.val == other.val and self.type == other.type

@attr.s(slots=True, frozen=True, hash=True)
class MatchResult:
    """The result of a comparison between two submissions.

    a - the ID of the first compared submission
    b - the ID of the second compared submission. Must be greater than `a`.
    score - bigger means more similar. The exact meaning depends on
        the comparator used.
    spans - a list of spans representing fragments that are shared
        between `a` and `b`.
    """

    a = attr.ib()
    b = attr.ib()
    score = attr.ib()
    spans = attr.ib(repr=False)


class SortedList(Sequence):
    def __init__(self, iter=None, key=lambda x: x):
        self.contents = sorted(iter, key=key) if iter is not None else []
        self.key = key

    @classmethod
    def from_sorted(cls, iter=None, key=lambda x: x):
        s_list = SortedList(key=key)
        if iter is not None:
            s_list.contents = list(iter)
        return s_list

    def __len__(self):
        return len(self.contents)

    def __getitem__(self, idx):
        return self.contents[idx]

    def bisect_key_right(self, x):
        lo = 0
        hi = len(self.contents)

        while lo < hi:
            mid = (lo + hi) // 2
            if x < self.key(self.contents[mid]):
                hi = mid
            else:
                lo = mid + 1
        return lo

    def bisect_key_left(self, x):
        lo = 0
        hi = len(self.contents)

        while lo < hi:
            mid = (lo + hi) // 2
            if self.key(self.contents[mid]) < x:
                lo = mid + 1
            else:
                hi = mid
        return lo
