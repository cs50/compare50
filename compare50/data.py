import abc
from collections.abc import Mapping, Sequence
import os
import pathlib
import numbers

import attr
import pygments
import pygments.lexers


__all__ = ["Pass", "Comparator", "File", "Submission", "Pass", "Span", "Score", "Comparison", "Token"]


class _PassRegistry(abc.ABCMeta):
    default = "StripAll"
    passes = {}
    def __new__(mcls, name, bases, attrs):
        cls = abc.ABCMeta.__new__(mcls, name, bases, attrs)

        if attrs.get("_{}__register".format(name), True):
            _PassRegistry.passes[name] = cls

        return cls

    @staticmethod
    def _get(name=None):
        if name is None:
            name = _PassRegistry.default
        return _PassRegistry.passes[name]

    @staticmethod
    def _get_all():
        return list(_PassRegistry.passes.values())


class Pass(metaclass=_PassRegistry):
    __register = False

    @abc.abstractmethod
    def preprocessors(self):
        pass

    @abc.abstractmethod
    def comparator(self):
        pass


class Comparator(metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def score(self, submissions, archive_submissions, ignored_files):
        pass

    @abc.abstractmethod
    def compare(self, scores, ignored_files):
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


@attr.s(slots=True, frozen=True)
class Submission:
    _store = IdStore(key=lambda sub: (sub.path, sub.files))

    path = attr.ib(converter=pathlib.Path, cmp=False)
    files = attr.ib(cmp=False)
    preprocessor = attr.ib(default=lambda tokens: tokens, cmp=False, repr=False)
    id = attr.ib(init=False)

    def __attrs_post_init__(self):
        object.__setattr__(self, "files", tuple([File(pathlib.Path(path), self) for path in self.files]))
        object.__setattr__(self, "id", Submission._store[self])

    def __iter__(self):
        return iter(self.files)

    @classmethod
    def get(cls, id):
        return cls._store.objects[id]


@attr.s(slots=True, frozen=True)
class File:
    _lexer_cache = {}
    _store = IdStore(key=lambda file: file.path)

    name = attr.ib(converter=pathlib.Path, cmp=False)
    submission = attr.ib(cmp=False)
    id = attr.ib(default=attr.Factory(lambda self: self._store[self], takes_self=True), init=False)

    @property
    def path(self):
        return self.submission.path / self.name

    def read(self, size=-1):
        with open(self.path) as f:
            return f.read(size)

    def tokens(self):
        return list(self.submission.preprocessor(self.unprocessed_tokens()))

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

    def unprocessed_tokens(self):
        text = self.read()
        lexer_tokens = self.lexer().get_tokens_unprocessed(text)
        tokens = []
        prevToken = None
        for token in lexer_tokens:
            if prevToken:
                tokens.append(Token(start=prevToken[0], end=token[0],
                                    type=prevToken[1], val=prevToken[2]))

            prevToken = token

        if prevToken:
            tokens.append(Token(start=prevToken[0], end=len(text),
                                type=prevToken[1], val=prevToken[2]))
        return tokens


@attr.s(slots=True, frozen=True, repr=False)
class Span:
    """
    Represents a range of characters in a particular file.
    file - the ID of the File containing the span
    start - the character index of the first character in the span
    end - the character index one past the end of the span
    """
    file = attr.ib()
    start = attr.ib()
    end = attr.ib()

    def __repr__(self):
        return "Span({} {}:{})".format(self.file.path.relative_to(self.file.submission.path.parent), self.start, self.end)

    def __contains__(self, other):
        return self.file == other.file and self.start <= other.start and self.end >= other.end

    def _raw_contents(self):
        return self.file.read()[self.start:self.end]


@attr.s(slots=True)
class Comparison:
    sub_a = attr.ib(validator=attr.validators.instance_of(Submission))
    sub_b = attr.ib(validator=attr.validators.instance_of(Submission))
    span_matches = attr.ib(factory=list)
    ignored_spans = attr.ib(factory=list)


@attr.s(slots=True)
class Score:
    sub_a = attr.ib(validator=attr.validators.instance_of(Submission), cmp=False)
    sub_b = attr.ib(validator=attr.validators.instance_of(Submission), cmp=False)
    score = attr.ib(default=0, validator=attr.validators.instance_of(numbers.Number))


def _sorted_subs(group):
    sub = None
    for span in group.spans:
        if not sub:
            sub = span.file.submission
        elif sub < span.file.submission:
            return (sub, span.file.submission)
        elif sub > span.file.submission:
            return (span.file.submission, sub)


@attr.s(slots=True, frozen=True)
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


@attr.s(slots=True)
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


class BisectList(Sequence):
    def __init__(self, iter=None, key=lambda x: x):
        self.contents = sorted(iter, key=key) if iter is not None else []
        self.key = key

    @classmethod
    def from_sorted(cls, iter=None, key=lambda x: x):
        s_list = BisectList(key=key)
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
