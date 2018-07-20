import winnowing
import pygments
import os
import pathlib
import bisect
from data import *
import pygments.lexers

@attr.s
class Submission:
    path = attr.ib(converter=pathlib.Path)
    preprocessor = attr.ib(default=lambda tokens: tokens)

    def files(self):
        for root, dirs, files in os.walk(self.path):
            for f in files:
                yield File((pathlib.Path(root) / f).relative_to(self.path), self)

@attr.s
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

        # add file and end index to create Tokens
        #tokens.append((len(text),))

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


def coarse_compare(submissions, distro_files, archive_submissions):
    """
    Take two submissions and return a tuple of dicts mapping files to
    lists of Fragments.  The id of `sub_a` must be less than that of
    `sub_b`.
    """
    submissions_index = winnowing.Index()
    archive_index = winnowing.Index()

    for sub in submissions:

        submissions_index.include()

    #distro = sub_a.upload.distro

    # map pass ids to MatchResults
    results = {}

    #for p in sub_a.upload.passes:
        #preprocessors, comparator = DEFAULT_CONFIG[p.config]

        #distro_files = p.upload.distro.files if distro else []

    preprocessors = []
    comparator = winnowing.Winnowing(10, 20)

    # keep tokens around for expanding spans

    tokens = {f.id: preprocess(tokenize(f), *preprocessors) for f in files_a + files_b} # + distro_files)


    # process files
    a_index = comparator.empty_index()
    b_index = comparator.empty_index()
    distro_index = comparator.empty_index()
    for files, index in [(files_a, a_index),
                         (files_b, b_index)]:
                         #(distro_files, distro_index)]:
        for f in files:
            index += comparator.index(f.id, f.submission.id, tokens[f.id], complete=True)

    # perform comparisons
    matches = a_index.compare(b_index)

    return matches

    #     # TODO
    #     if matches:
    #         matches = expand_spans(matches[0], tokens)
    #     else:
    #         # no matches, create empty MatchResult to hold distro code
    #         matches = MatchResult(sub_a.id, sub_b.id, {})
    #     if distro:
    #         # add expanded distro spans to match as group "distro"
    #         for index in a_index, b_index:
    #             distro_match = distro_index.compare(index)
    #             if distro_match:
    #                 distro_match = expand_spans(distro_match[0], tokens)
    #                 distro_spans = [span
    #                                 for spans in distro_match.spans.values()
    #                                 for span in spans
    #                                 if File.query.get(span.file).submission_id != distro.id]
    #                 matches.spans.setdefault("distro", []).extend(distro_spans)
    #
    #     results[p.id] = matches
    #
    # return flatten_spans(results)

if __name__ == "__main__":
    sub_a = Submission("files/")
    file_a = File("foo.py", sub_a)
    #print(list(file_a.tokens()))
    #print(sub_a)
    print(list(sub_a.files()))


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
