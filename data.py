class Token:
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
    __slots__ = ["_a", "_b", "_score", "_fragments"]
    def __init__(self, a, b, score, fragments):
        self._a = a
        self._b = b
        self._score = score
        self._fragments = fragments

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
    def fragments(self):
        return self._fragments


class Span:
    __slots__ = ["_start", "_stop", "_file", "_hash"]
    def __init__(self, start, stop, file, hash):
        self._start = start
        self._stop = stop
        self._file = file
        self._hash = hash

    @property
    def start(self):
        return self._start

    @property
    def stop(self):
        return self._stop

    @property
    def file(self):
        return self._file

    @property
    def hash(self):
        return self._hash

    def __repr__(self):
        return f"Span({self.file}:{self.start}:{self.stop})"

class Fragment:
    """A fragment of text with a collection of group ids identifying which
    match groups it belongs to for which passes.
    """
    def __init__(self, groups, text):
        self._groups = groups
        self._text = text

    @property
    def groups(self):
        return self._groups

    @property
    def text(self):
        return self._text
