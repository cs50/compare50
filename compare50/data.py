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
    _span_matches = attr.ib(default=attr.Factory(list))

    def add(self, span_a, span_b):
        if self._span_matches and span_a.file != self._span_matches[0][0].file:
            span_match = (span_b, span_a)
        else:
            span_match = (span_a, span_b)
        self._span_matches.append(span_match)

    def expand(self):
        """Returns a new MatchResult with maximally expanded spans.
        match - the MatchResult containing spans to expand
        tokens - a dict mapping files to lists of their tokens
        """
        if not self._span_matches:
            return self

        tokens_a = list(self._span_matches[0][0].file.tokens())
        tokens_b = list(self._span_matches[0][1].file.tokens())

        for span_a, span_b in self._span_matches:
            # TODO check that both spans aren't already absorbed by another expanded span
            #     set other (if not absorbed) to match
            # TODO expand left
            # TODO expand right
            pass

        # start_cache = {}
        #
        # tokens = {self._span_matches[0][0].file : list(self._span_matches[0][0].file.tokens()),
        #           self._span_matches[0][1].file : list(self._span_matches[0][1].file.tokens())}
        #
        # # binary search to find index of token with given start
        # def get_index(file, start):
        #     starts = start_cache.get(file)
        #     if starts is None:
        #         starts = [t.start for t in tokens[file]]
        #         start_cache[file] = starts
        #     return bisect.bisect_left(starts, start)
        #
        # new_spans = {}
        # for spans in self._span_matches:
        #     # if there exists an expanded group
        #     # for which all current spans are contained
        #     # in some expanded span, then skip this group
        #
        #     if any(all(any(span.file == other.file and \
        #                    span.start >= other.start and \
        #                    span.stop <= other.stop
        #                    for other in expanded)
        #                for span in spans)
        #            for expanded in new_spans.values()):
        #         continue
        #
        #     # first, last index into file's tokens for each span
        #     indices = {span: (get_index(span.file, span.start),
        #                       get_index(span.file, span.stop) - 1)
        #                for span in spans}
        #
        #     while True:
        #         changed = False
        #         # find previous and next tokens for each span
        #         prevs = set(tokens[span.file][first - 1].val if first > 0 else None
        #                     for span, (first, last) in indices.items())
        #         nexts = set((tokens[span.file][last + 1].val
        #                      if last + 1 < len(tokens[span.file]) else None)
        #                     for span, (first, last) in indices.items())
        #
        #         # expand front of spans
        #         if len(prevs) == 1 and prevs.pop() is not None:
        #             changed = True
        #             indices = {span: (first - 1, last)
        #                        for span, (first, last) in indices.items()}
        #             # expand back of spans
        #         if len(nexts) == 1 and nexts.pop() is not None:
        #             changed = True
        #             indices = {span: (start, stop + 1)
        #                        for span, (start, stop) in indices.items()}
        #         if not changed:
        #             break
        #
        #     new_spans[group_id] = [Span(span.file,
        #                                 tokens[span.file][first].start,
        #                                 tokens[span.file][last].stop)
        #                            for span, (first, last) in indices.items()]
        # return MatchResult(match.a, match.b, match.score, new_spans)

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
