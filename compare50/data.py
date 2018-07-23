import attr
import os
import pygments
import pygments.lexers
import abc
import pathlib

class Comparator(metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def cross_compare(self, submissions, archive_submissions, ignored_files):
        pass

    @abc.abstractmethod
    def create_spans(self, file1, file2, ignored_files):
        pass


@attr.s(slots=True, frozen=True, hash=True)
class Submission:
    path = attr.ib(converter=pathlib.Path)
    preprocessor = attr.ib(default=lambda tokens: tokens, hash=False)

    def files(self):
        for root, dirs, files in os.walk(self.path):
            for f in files:
                yield File((pathlib.Path(root) / f).relative_to(self.path), self)


@attr.s(slots=True, frozen=True, hash=True)
class File:
    name = attr.ib()
    submission = attr.ib()

    @property
    def path(self):
        return self.submission.path / self.name

    def tokens(self):
        return self.submission.preprocessor(self._tokenize())

    def _tokenize(self):
        with open(self.path, "r")  as f:
            text = f.read()

        # get lexer for this file type
        try:
            lexer = pygments.lexers.get_lexer_for_filename(self.path)
        except pygments.util.ClassNotFound:
            try:
                lexer = pygments.lexers.guess_lexer(text)
            except pygments.util.ClassNotFound:
                lexer = pygments.lexers.special.TextLexer()

        # tokenize file into (start, type, value) tuples
        tokens = lexer.get_tokens_unprocessed(text)

        prevToken = None

        for token in tokens:
            if prevToken:
                yield Token(start=prevToken[0], end=token[0],
                            type=prevToken[1], val=prevToken[2])

            prevToken = token

        if prevToken:
            yield Token(start=prevToken[0], end=len(text),
                        type=prevToken[1], val=prevToken[2])


@attr.s(slots=True, frozen=True)
class FileMatch:
    file_a = attr.ib()
    file_b = attr.ib()
    score = attr.ib()


@attr.s(slots=True)
class SpanMatches:
    _span_matches = attr.ib(default=attr.Factory(list), converter=list)

    def add(self, span_a, span_b):
        if self._span_matches and span_a.file != self._span_matches[0][0].file:
            span_match = (span_b, span_a)
        else:
            span_match = (span_a, span_b)
        self._span_matches.append(span_match)

    def expand(self):
        """
        Expand all spans in this SpanMatches.
        returns a new instance of SpanMatches with maximally extended spans.
        """
        if not self._span_matches:
            return self

        tokens_a = list(self._span_matches[0][0].file.tokens())
        tokens_b = list(self._span_matches[0][1].file.tokens())

        start_to_index_a = {t.start:i for i, t in enumerate(tokens_a)}
        start_to_index_b = {t.start:i for i, t in enumerate(tokens_b)}

        expanded_span_pairs = set()

        for span_a, span_b in self._span_matches:
            index_a = start_to_index_a[span_a.start]
            index_b = start_to_index_b[span_b.start]

            # TODO decide if "optimisation" actually adds/optimizes anything
            # TODO check that both spans aren't already absorbed by another expanded span
            #     set other (if not absorbed) to match
            # for exp_span_a, exp_span_b in expanded_spans:
            #    if absorbs(exp_span_a, span_a) and absorbs(exp_span_b, span_b):
            #        pass

            # Expand left
            left_diff = -1
            try:
                while tokens_a[index_a - left_diff] == tokens_b[index_b - left_diff]:
                    left_diff -= 1
            except IndexError:
                pass
            left_diff += 1

            # Expand right
            right_diff = 1
            try:
                while tokens_a[index_a + right_diff] == tokens_b[index_b + right_diff]:
                    right_diff += 1
            except IndexError:
                pass
            right_diff -= 1

            # Add new spans
            expanded_span_pairs.add(
                (Span(span_a.file, tokens[index_a - left_diff].start, tokens[index_a + right_diff].end),
                Span(span_b.file, tokens[index_b - left_diff].start, tokens[index_b + right_diff].end))
            )

        return SpanMatches(expanded_span_pairs)

    def __iter__(self):
        return iter(self._span_matches)


@attr.s(slots=True, frozen=True)
class SubmissionMatch:
    sub_a = attr.ib()
    sub_b = attr.ib()
    file_matches = attr.ib()

    @property
    def score(self):
        return sum(file_match.score for file_match in self.file_matches)


@attr.s(slots=True, hash=True, frozen=True)
class Group:
    spans = attr.ib(converter=frozenset)


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
    end = attr.ib()
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


@attr.s(slots=True, frozen=True, hash=True, repr=False)
class Span:
    """Represents a range of characters in a particular file.

    file - the ID of the File containing the span
    start - the character index of the first character in the span
    stop - the character index one past the end of the span
    """
    file = attr.ib()
    start = attr.ib()
    stop = attr.ib()

    def __repr__(self):
        return f"Span({self.file.name} {self.start}:{self.stop})"
