import abc
from collections.abc import Mapping, Sequence
import os
import pathlib
import numbers

import attr
import pygments
import pygments.lexers


__all__ = ["Pass", "Comparator", "File", "Submission",
           "Pass", "Span", "Score", "Comparison", "Token"]


class _PassRegistry(abc.ABCMeta):
    passes = {}

    def __new__(mcls, name, bases, attrs):
        cls = abc.ABCMeta.__new__(mcls, name, bases, attrs)

        if attrs.get("_{}__register".format(name), True):
            _PassRegistry.passes[name] = cls

        return cls

    @staticmethod
    def _get(name):
        return _PassRegistry.passes[name]

    @staticmethod
    def _get_all():
        return list(_PassRegistry.passes.values())


class Pass(metaclass=_PassRegistry):
    """
    Abstract base class for ``compare50`` passes, which are essentially ways for
    ``compare50`` to compare submissions. Subclasses must define a list of preprocessors
    (functions from tokens to tokens which will be run on every file ``compare50``
    recieves) as well as a comparator (used to score and compare the preprocessed
    submissions).
    """
    __register = False

    @abc.abstractmethod
    def preprocessors(self):
        pass

    @abc.abstractmethod
    def comparator(self):
        pass


class Comparator(metaclass=abc.ABCMeta):
    """
    Abstract base class for ``compare50`` comparators which specify how submissions
    should be scored and compared.
    """
    @abc.abstractmethod
    def score(self, submissions, archive_submissions, ignored_files):
        """
        Given a list of submissions, a list of archive submissions, and a set of distro
        files, return a list of :class:`compare50.Score`\ s for each submission pair.
        """
        pass

    @abc.abstractmethod
    def compare(self, scores, ignored_files):
        """
        Given a list of scores and a list of distro files, perform an in-depth
        comparison of each submission pair and return a corresponding list of
        :class:`compare50.Comparison`\ s
        """
        pass


class IdStore(Mapping):
    """
    Mapping from objects to IDs. If object has not been added to the store,
    a new id is generated for it.
    """
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
    """
    :ivar path: the file path of the submission
    :ivar files: list of :class:`compare50.File` objects contained in the submission
    :ivar preprocessor: A function from tokens to tokens that will be run on \
            each file in the submission
    :ivar id: integer that uniquely identifies this submission \
            (submissions with the same path will always have the same id).

    Represents a single submission. Submissions may either be single files or
    directories containing many files.
    """
    _store = IdStore(key=lambda sub: (sub.path, sub.files))

    path = attr.ib(converter=pathlib.Path, cmp=False)
    files = attr.ib(cmp=False)
    preprocessor = attr.ib(default=lambda tokens: tokens, cmp=False, repr=False)
    is_archive = attr.ib(default=False, cmp=False)
    id = attr.ib(init=False)

    def __attrs_post_init__(self):
        object.__setattr__(self, "files", tuple(
            [File(pathlib.Path(path), self) for path in self.files]))
        object.__setattr__(self, "id", Submission._store[self])

    def __iter__(self):
        return iter(self.files)

    @classmethod
    def get(cls, id):
        """Retrieve submission corresponding to specified id"""
        return cls._store.objects[id]


@attr.s(slots=True, frozen=True)
class File:
    """
    :ivar name: file name (path relative to the submission path)
    :ivar submission: submission containing this file
    :ivar id: integer that uniquely identifies this file (files with the same path \
            will always have the same id)


    Represents a single file from a submission.
    """
    _lexer_cache = {}
    _store = IdStore(key=lambda file: file.path)

    name = attr.ib(converter=pathlib.Path, cmp=False)
    submission = attr.ib(cmp=False)
    id = attr.ib(default=attr.Factory(lambda self: self._store[self], takes_self=True), init=False)

    @property
    def path(self):
        """The full path of the file"""
        return self.submission.path / self.name

    def read(self, size=-1):
        """Open file, read ``size`` bytes from it, then close it."""
        with open(self.path) as f:
            return f.read(size)

    def tokens(self):
        """Returns the preprpocessed tokens of the file."""
        return list(self.submission.preprocessor(self.unprocessed_tokens()))

    def lexer(self):
        """Determine which Pygments lexer should be used."""
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
        """Find File with given id"""
        return cls._store.objects[id]

    def unprocessed_tokens(self):
        """Get the raw tokens of the file."""
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
    :ivar file: the ID of the File containing the span
    :ivar start: the character index of the first character in the span
    :ivar end: the character index one past the end of the span


    Represents a range of characters in a particular file.
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
    """
    :ivar sub_a: the first submission
    :ivar sub_b: the second submission
    :ivar span_matches: a list of pairs of matching :class:`compare50.Span`\ s, wherein \
            the first element of each pair is from ``sub_a`` and the second is from \
            ``sub_b``.
    :ivar ignored_spans: a list of :class:`compare50.Span`\ s which were ignored \
            (e.g. because they matched distro files)

    Represents an in-depth comparison of two submissions.
    """
    sub_a = attr.ib(validator=attr.validators.instance_of(Submission))
    sub_b = attr.ib(validator=attr.validators.instance_of(Submission))
    span_matches = attr.ib(factory=list)
    ignored_spans = attr.ib(factory=list)


@attr.s(slots=True)
class Score:
    """
    :ivar sub_a: the first submission
    :ivar sub_b: the second submission
    :ivar score: a number indicating the similarity between ``sub_a`` and ``sub_b``\
            (higher meaning more similar)

    A score representing the similarity of two submissions.
    """
    sub_a = attr.ib(validator=attr.validators.instance_of(Submission), cmp=False)
    sub_b = attr.ib(validator=attr.validators.instance_of(Submission), cmp=False)
    score = attr.ib(default=0, validator=attr.validators.instance_of(numbers.Number))


@attr.s(slots=True)
class Compare50Result:
    """
    :ivar pass_: the pass that was used to compare the two submissions
    :ivar score: the :class:`compare50.Score` generated when the subimssions were scored
    :ivar groups: a list of groups of matching spans
    :ivar ignored_spans: a list of spans that were ignored during the comparison

    The final result of comparing two submissions that is passed to the renderer.
    """
    pass_ = attr.ib()
    score = attr.ib()
    groups = attr.ib()
    ignored_spans = attr.ib()

    @property
    def name(self):
        """The name of the pass that was run to compare the submissions."""
        return self.pass_.__name__

    @property
    def sub_a(self):
        """The 'first' (left) submission"""
        return self.score.sub_a

    @property
    def sub_b(self):
        """The 'second' (right) submission"""
        return self.score.sub_b


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
    """
    :ivar spans: spans with identical contents

    A group of spans with matching contents
    """
    spans = attr.ib(converter=frozenset)
    _subs = attr.ib(init=False, default=attr.Factory(_sorted_subs, takes_self=True))

    @property
    def sub_a(self):
        """The 'first' submission represented in the group (i.e. the one with
        the smaller identifier)"""
        return self._subs[0]

    @property
    def sub_b(self):
        """The 'second' submission represented in the group (i.e. the one with
        the larger identifier)"""
        return self._subs[1]


@attr.s(slots=True)
class Token:
    """
    :ivar start: the character index of the beginning of the token
    :ivar end: the character index one past the end of the token
    :ivar type: the Pygments token type
    :ivar val: the string contents of the token

    A result of the lexical analysis of a file. Preprocessors operate
    on Token streams.
    """
    start = attr.ib(cmp=False)
    end = attr.ib(cmp=False)
    type = attr.ib()
    val = attr.ib()

    def __eq__(self, other):
        # Note that there is no sanity checking. Sacrificed for performance.
        return self.val == other.val and self.type == other.type


class BisectList(Sequence):
    """
    A sorted list allowing for easy binary seaching. This exists because Python's
    bisect does not allow you to compare objects via a key function.
    """
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
