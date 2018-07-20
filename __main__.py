import winnowing
import pygments
import os
import pathlib
import bisect
import heapq
import collections
from data import *
import pygments.lexers

@attr.s(slots=True, hash=True)
class Submission:
    path = attr.ib(converter=pathlib.Path)
    preprocessor = attr.ib(default=lambda tokens: tokens, hash=False)

    def files(self):
        for root, dirs, files in os.walk(self.path):
            for f in files:
                yield File((pathlib.Path(root) / f).relative_to(self.path), self)

@attr.s(slots=True, hash=True)
class File:
    name = attr.ib()
    submission = attr.ib(hash=False)

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
                yield Token(start=prevToken[0], stop=token[0],
                            type=prevToken[1], val=prevToken[2])

            prevToken = token

        if prevToken:
            yield Token(start=prevToken[0], stop=len(text),
                        type=prevToken[1], val=prevToken[2])

def expand_spans(match, tokens):
    """Returns a new MatchResult with maximally expanded spans.

    match - the MatchResult containing spans to expand
    tokens - a dict mapping files to lists of their tokens
    """
    # lazily map files to lists of token start indices
    start_cache = {}

    # binary search to find index of token with given start
    def get_index(file, start):
        starts = start_cache.get(file)
        if starts is None:
            starts = [t.start for t in tokens[file]]
            start_cache[file] = starts
        return bisect.bisect_left(starts, start)

    new_spans = {}
    for group_id, spans in match.spans.items():
        # if there exists an expanded group
        # for which all current spans are contained
        # in some expanded span, then skip this group
        if any(all(any(span.file == other.file and \
                       span.start >= other.start and \
                       span.stop <= other.stop
                       for other in expanded)
                   for span in spans)
               for expanded in new_spans.values()):
            continue
        # first, last index into file's tokens for each span
        indices = {span: (get_index(span.file, span.start),
                          get_index(span.file, span.stop) - 1)
                   for span in spans}

        while True:
            changed = False
            # find previous and next tokens for each span
            prevs = set(tokens[span.file][first - 1].val if first > 0 else None
                        for span, (first, last) in indices.items())
            nexts = set((tokens[span.file][last + 1].val
                         if last + 1 < len(tokens[span.file]) else None)
                        for span, (first, last) in indices.items())

            # expand front of spans
            if len(prevs) == 1 and prevs.pop() is not None:
                changed = True
                indices = {span: (first - 1, last)
                           for span, (first, last) in indices.items()}
                # expand back of spans
            if len(nexts) == 1 and nexts.pop() is not None:
                changed = True
                indices = {span: (start, stop + 1)
                           for span, (start, stop) in indices.items()}
            if not changed:
                break

        new_spans[group_id] = [Span(span.file,
                                    tokens[span.file][first].start,
                                    tokens[span.file][last].stop)
                               for span, (first, last) in indices.items()]
    return MatchResult(match.a, match.b, match.score, new_spans)


def flatten_spans(matches):
    """Return a pair of dicts mapping Files to lists of Fragments. Each
    list of Fragments is the fragmented contents of an entire file.

    match - a dict mapping pass IDs to MatchResults
    """
    # separate spans by submission
    a_spans = {}
    b_spans = {}
    for pass_id, match in matches.items():
        for group, spans in match.spans.items():
            for span in spans:
                if span.file.submission.id == match.a:
                    spans = a_spans
                elif span.file.submission.id == match.b:
                    spans = b_spans
                else:
                    assert false, "Span from unknown submission in match"
                spans.setdefault(pass_id, {}) \
                    .setdefault(group, []) \
                    .append(span)

    a_results = {}
    b_results = {}
    for spans, results in (a_spans, a_results), (b_spans, b_results):
        # separate by file, move pass_id and group into tuple
        by_file = {}
        for pass_id, spans in spans.items():
            for group, spans in spans.items():
                for span in spans:
                    entry = by_file.setdefault(span.file, [])
                    entry.append((span, pass_id, group))

        for file, span_data in by_file.items():
            # iterate through text, creating list of Fragments
            file_results = []
            span_data.sort(key=lambda s: s[0].start)
            with open(File.query.get(file).full_path, "r") as f:
                text = f.read()
            current_spans = []
            current_text = []

            def create_frag():
                groups = {}
                for span, pass_id, group in current_spans:
                    groups.setdefault(pass_id, []).append(group)
                    if "distro" in groups[pass_id]:
                        groups[pass_id] = ["distro"]
                file_results.append(Fragment(groups, "".join(current_text)))

            for i, c in enumerate(text):
                # calculate new current groups
                new_spans = [(span, pass_id, group)
                             for span, pass_id, group in current_spans
                             if span.stop > i]
                while span_data and span_data[0][0].start == i:
                    new_spans.append(span_data.pop(0))

                # emit fragment if span would end or start
                if new_spans != current_spans:
                    create_frag()
                    current_text = []
                current_spans = new_spans
                current_text.append(c)

            # final fragment, possibly empty
            create_frag()
            results[file] = file_results

    return a_results, b_results

@attr.s(slots=True, frozen=True)
class FileMatch:
    file_a = attr.ib()
    file_b = attr.ib()
    score = attr.ib()

@attr.s(slots=True, frozen=True)
class SubmissionMatch:
    sub_a = attr.ib()
    sub_b = attr.ib()
    file_matches = attr.ib()

    @property
    def score(self):
        return sum(file_match.score for file_match in self.file_matches)

@attr.s(slots=True)
class SpanMatches:
    _span_matches = attr.ib(default=[])

    def add(self, span_a, span_b):
        if self._span_matches and span_a.file != self._span_matches[0].file:
            span_match = (span_b, span_a)
        else:
            span_match = (span_b, span_a)
        self._span_matches.append(span_match)

    def expand(self):
        return self

    def __iter__(self):
        return iter(self._span_matches)

@attr.s(slots=True)
class Group:
    spans = attr.ib(default=[])

def rank_submissions(submissions, distro_files, archive_submissions, index, n=50):
    """"""

    submissions_index = index()
    archive_index = index()

    # Index all submissions
    for sub in submissions:
        for file in sub.files():
            submissions_index.union(index(file=file))

    # Index all archived submissions
    for sub in archive_submissions:
        for file in sub.files():
            archive_index.union(index(file=file))

    # Ignore all files from distro
    for file in distro_files:
        submissions_index.ignore(file)
        archive_index.ignore(file)

    # Add submissions to archive (the Index we're going to compare against)
    archive_index.union(submissions_index)

    # TODO results = submissions_index.cross_compare(archive_index)
    results = [FileMatch(list(submissions[0].files())[0], list(submissions[1].files())[0], 10), \
                FileMatch(list(submissions[1].files())[0], list(submissions[2].files())[0], 20)]

    # Link submission pairs to file matches
    submissions_file_matches = {}
    for file_match in results:
        key = frozenset([file_match.file_a.submission, file_match.file_b.submission])
        val = submissions_file_matches.get(key, [])
        val.append(file_match)
        submissions_file_matches[key] = val

    # Create submission matches
    submission_matches = []
    for sub_pair, file_matches in submissions_file_matches.items():
        sub_a, sub_b = tuple(sub_pair)
        submission_matches.append(SubmissionMatch(sub_a, sub_b, file_matches))

    # Keep only top `n` submission matches
    return heapq.nlargest(n, submission_matches, lambda sub_match : sub_match.score)

def create_spans(submission_matches, index):
    for sub_match in submission_matches:
        # Create `SpanMatches` for all `FileMatch`es
        span_matches_list = []
        for file_match in sub_match.file_matches:
            span_matches = index.create_spans(file_match.file_a, file_match.file_b)
            span_matches.flatten()
            span_matches_list.append(span_matches)

        yield group(span_matches_list)

def group_spans(span_matches_list):
    """
    Transforms a list of SpanMatches into a list of Groups.
    Finds all spans that share the same content, and groups them in one Group.
    returns a list of Groups.
    """

    # Generate fictive content by which we can identify spans
    def content_factory():
        content_factory.i += 1
        return content_factory.i
    content_factory.i = -1

    # Map a span to its content
    span_to_content = collections.defaultdict(content_factory)
    # Group spans by content
    content_to_spans = collections.defaultdict(lambda : set())

    for span_matches in span_matches_list:
        for span_a, span_b in span_matches:
            # Get contents of span_a
            content_a = span_to_content[span_a]

            # If span_b has no contents, give it span_a's contents
            if span_b not in span_to_content:
                content_b = span_to_content[span_a]
                span_to_content[span_b] = content_b
            # Otherwise, retrieve span_b's contents
            else:
                content_b = span_to_content[span_b]

            # If content_a is higher (older) than content_b
            if content_a > content_b:
                # Set all spans that share content_a to instead contain content_b
                for span in content_to_spans[content_a]:
                    content_to_spans[content_b].add(span)
                    span_to_content[span] = content_b
                # Delete content_a
                del content_to_spans[content_a]
            # Otherwise if content_b is higher (older) than content_a
            elif content_a < content_b:
                # Set all spans that share content_b to instead contain content_a
                for span in content_to_spans[content_b]:
                    content_to_spans[content_a].add(span)
                    span_to_content[span] = content_a
                # Delete content_b
                del content_to_spans[content_b]

            # Add span_a and span_b to content maps
            content = min(content_a, content_b)
            span_to_content[span_a] = content
            span_to_content[span_b] = content
            content_to_spans[content].add(span_a)
            content_to_spans[content].add(span_b)

    return [Group(spans) for spans in content_to_spans.values()]

if __name__ == "__main__":
    sub_a = Submission("files/sub_a")
    sub_b = Submission("files/sub_b")
    sub_c = Submission("files/sub_c")

    # TODO index = config.parser.index
    #index = winnowing.Index

    #submission_matches = rank_submissions([sub_a, sub_b, sub_c], [], [], index)
    #print(submission_matches)
    #spans = create_spans(submission_matches)
    #print(spans)

    span_matches_1 = SpanMatches()
    span_matches_1._span_matches = [(i, i + 1) for i in range(10)]

    span_matches_2 = SpanMatches()
    span_matches_2._span_matches = [(11 + i, 11 + i + 1) for i in range(10)]

    span_matches_3 = SpanMatches()
    span_matches_3._span_matches = [(12, 15)]

    groups = group_spans([span_matches_1, span_matches_2, span_matches_3])
    print(groups)
    #print(list(file_a.tokens()))
    #print(sub_a)
    #print(list(sub_a.files()))


# sub_1 = Submission(1)
# sub_2 = Submission(2)
#
# file_10 = File(10, pathlib.Path("files/foo.py").absolute(), sub_1)
# file_20 = File(20, pathlib.Path("files/bar.py").absolute(), sub_2)
#
# c = compare([file_10], [file_20])
#
# spans = expand_spans(c[0], {file_10.id: tokenize(file_10), file_20.id: tokenize(file_20)})
# spans_2 = flatten_spans({100: spans})
# print(c)
# print()
# print(spans)
