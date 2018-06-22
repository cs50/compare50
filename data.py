class Token:
    """A result of the lexical analysis of a file. Preprocessors operate
    on Token streams.

    start - the character index of the beginning of the token
    stop - the character index one past the end of the token
    type - the Pygments token type
    val - the string contents of the token
    """
    __slots__ = ["_start", "_stop", "_type", "_val"]

    def __init__(self, other=None, file=None, start=None, stop=None,
                 type=None, val=None):
        self._start = start if start is not None else other.start
        self._stop = stop if stop is not None else other.stop
        self._type = type if type is not None else other.type
        self._val = val if val is not None else other.val

    @property
    def start(self):
        return self._start

    @property
    def stop(self):
        return self._stop

    @property
    def type(self):
        return self._type

    @property
    def val(self):
        return self._val

    def __repr__(self):
        return (f"Token({self.file.id}, {self.start}, {self.stop}, "
                f"{self.type}, {self.val})")


class MatchResult:
    """The result of a comparison between two submissions.

    a - the ID of the first compared submission
    b - the ID of the second compared submission. Must be greater than `a`.
    score - bigger means more similar. The exact meaning depends on
        the comparator used.
    spans - a list of spans representing fragments that are shared
        between `a` and `b`.
    """
    __slots__ = ["_a", "_b", "_score", "_spans"]

    def __init__(self, a, b, score, spans):
        self._a = a
        self._b = b
        self._score = score
        self._spans = spans

    @property
    def a(self):
        return self._a

    @property
    def b(self):
        return self._b

    @property
    def score(self):
        return self._score

    @property
    def spans(self):
        return self._spans


class Span:
    """Represents a range of characters in a particular file.

    file - the File containing the span
    start - the character index of the first character in the span
    stop - the character index one past the end of the span
    """
    __slots__ = ["_file", "_start", "_stop"]

    def __init__(self, file, start, stop):
        self._file = file
        self._start = start
        self._stop = stop

    @property
    def start(self):
        return self._start

    @property
    def stop(self):
        return self._stop

    @property
    def file(self):
        return self._file

    def __repr__(self):
        return f"Span({self.file}:{self.start}:{self.stop})"


class Fragment:
    """A fragment of text with a collection of group ids identifying which
    match groups it belongs to for which passes.

    groups - a dict mapping pass ids to lists of group ids
    text - a string, the contents of this fragment
    """
    __slots__ = ["_groups", "_text"]

    def __init__(self, groups, text):
        self._groups = groups
        self._text = text

    @property
    def groups(self):
        return self._groups

    @property
    def text(self):
        return self._text
