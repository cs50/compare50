import abc
from itertools import islice
import os
import pathlib

import attr
import pygments
import pygments.lexers
from sortedcontainers import SortedList


class Comparator(metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def cross_compare(self, submissions, archive_submissions, ignored_files):
        pass

    @abc.abstractmethod
    def create_spans(self, matches, ignored_files):
        pass


class _IdStore:
    def __init__(self, key=lambda obj: obj):
        self.ids = {}
        self.max_id = 0
        self.objs = {}
        self.key = key

    def id(self, obj):
        key = self.key(obj)
        if key not in self.ids:
            self.ids[key] = self.max_id
            self.objs[self.max_id] = obj
            self.max_id += 1
        return self.ids[key]


@attr.s(slots=True, frozen=True, hash=True)
class Submission:
    _store = _IdStore(key=lambda sub: sub.path)

    path = attr.ib(converter=pathlib.Path, hash=False, cmp=False)
    preprocessor = attr.ib(default=lambda tokens: tokens, hash=False, cmp=False)
    id = attr.ib(default=attr.Factory(lambda self: self._store.id(self), takes_self=True), init=False)
    file_paths = attr.ib(default=tuple(), hash=False, cmp=False)

    def files(self):
        if self.file_paths:
            for file_path in self.file_paths:
                yield File(file_path, self)
            return

        for root, dirs, files in os.walk(str(self.path)):
            for f in files:
                yield File((pathlib.Path(root) / f).relative_to(self.path), self)

    @classmethod
    def get(cls, id):
        return cls._store.objs[id]

    @staticmethod
    def from_file_path(path, preprocessor):
        path = pathlib.Path(path).absolute()
        return Submission(path.parent, preprocessor, file_paths=[path.name])


@attr.s(slots=True, frozen=True, hash=True)
class File:
    _lexer_cache = {}
    _store = _IdStore(key=lambda file: file.path)

    name = attr.ib(converter=pathlib.Path, cmp=False, hash=False)
    submission = attr.ib(cmp=False, hash=False)
    id = attr.ib(default=attr.Factory(lambda self: self._store.id(self), takes_self=True), init=False)

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
        return cls._store.objs[id]


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

    def expand(self):
        """
        Expand all spans in this SpanMatches.
        returns a new instance of SpanMatches with maximally extended spans.
        """
        if not self._matches:
            return

        expanded_span_pairs = set()

        tokens_a = SortedList(self.file_a.tokens(), key=lambda tok: tok.start)
        tokens_b = SortedList(self.file_b.tokens(), key=lambda tok: tok.start)


        for span_a, span_b in self._matches:
            # index_a = start_to_index_a[span_a.start]
            # index_b = start_to_index_b[span_b.start]

            # TODO decide if "optimisation" actually adds/optimizes anything
            # TODO check that both spans aren't already absorbed by another expanded span
            #     set other (if not absorbed) to match
            # for exp_span_a, exp_span_b in expanded_spans:
            #    if absorbs(exp_span_a, span_a) and absorbs(exp_span_b, span_b):
            #        pass

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
