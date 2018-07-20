import attr

@attr.s(slots=True, frozen=True)
class Token:
    """A result of the lexical analysis of a file. Preprocessors operate
    on Token streams.

    start - the character index of the beginning of the token
    stop - the character index one past the end of the token
    type - the Pygments token type
    val - the string contents of the token
    """
    start = attr.ib()
    stop = attr.ib()
    type = attr.ib()
    val = attr.ib()


@attr.s(slots=True, frozen=True)
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


@attr.s(slots=True, frozen=True)
class Span:
    """Represents a range of characters in a particular file.

    file - the ID of the File containing the span
    start - the character index of the first character in the span
    stop - the character index one past the end of the span
    """
    file = attr.ib()
    start = attr.ib()
    stop = attr.ib()


@attr.s(slots=True, frozen=True)
class Fragment:
    """A fragment of text with a collection of group ids identifying which
    match groups it belongs to for which passes.

    groups - a dict mapping pass ids to lists of group ids
    text - a string, the contents of this fragment
    """
    groups = attr.ib()
    text = attr.ib()
