import collections
import concurrent.futures as futures
import heapq
import os
import pathlib

from pygments import highlight
from pygments.formatters import HtmlFormatter

from .data import *

def render(groups, dest):
    dest = pathlib.Path(dest)

    if not dest.exists():
        os.mkdir(dest)

    subs_to_groups = collections.defaultdict(list)

    for group in groups:
        subs_to_groups[(group.sub_a, group.sub_b)].append(group)

    for i, subs in enumerate(subs_to_groups):
        sub_a, sub_b = subs
        with open(dest / "match_{}.html".format(i), "w") as f:
            f.write("{} {}<br/>".format(sub_a.path, sub_b.path))

            for group in subs_to_groups[subs]:
                f.write(" ".join(str(span) for span in group.spans))
                f.write("<br/>")

            for sub in subs:
                for file in sub.files():
                    with open(file.path) as in_file:
                        f.write(highlight(in_file.read(), file.lexer(), HtmlFormatter()))


def rank_submissions(submissions, archive_submissions, ignored_files, comparator, n=50):
    """"""
    results = comparator.cross_compare(submissions, archive_submissions, ignored_files)

    # Link submission pairs to file matches
    #submissions_file_matches = collections.defaultdict(list)
    sub_ids_to_file_matches = collections.defaultdict(list)
    for file_match in results:
        sub_id1, sub_id2 = file_match.file_a.submission.id, file_match.file_b.submission.id

        if sub_id1 == sub_id2:
            continue
        elif sub_id1 < sub_id2:
            key = sub_id1, sub_id2
        else:
            key = sub_id2, sub_id1

        sub_ids_to_file_matches[key].append(file_match)

    # Create submission matches
    submission_matches = [SubmissionMatch(Submission.get(sub_id_a), Submission.get(sub_id_b), file_matches)
                          for (sub_id_a, sub_id_b), file_matches in sub_ids_to_file_matches.items()]

    # Keep only top `n` submission matches
    return heapq.nlargest(n, submission_matches, lambda sub_match : sub_match.score)

def _expand(span_matches):
    return span_matches.expand()

def create_groups(submission_matches, comparator, ignored_files):
    file_matches = [fm for sm in submission_matches for fm in sm.file_matches]

    sub_match_to_span_matches = collections.defaultdict(list)
    span_matches_list = list(comparator.create_spans(file_matches, ignored_files))

    groups = []
    with futures.ProcessPoolExecutor() as executor:
        for span_matches in executor.map(_expand, span_matches_list):
            sub_match_to_span_matches[(span_matches.file_a.submission.id, span_matches.file_b.submission.id)].append(span_matches)

        for gs in executor.map(group_spans, sub_match_to_span_matches.values()):
            groups.extend(gs)

    return groups


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


# def expand_spans(match, tokens):
#     """Returns a new MatchResult with maximally expanded spans.
#
#     match - the MatchResult containing spans to expand
#     tokens - a dict mapping files to lists of their tokens
#     """
#     # lazily map files to lists of token start indices
#     start_cache = {}
#
#     # binary search to find index of token with given start
#     def get_index(file, start):
#         starts = start_cache.get(file)
#         if starts is None:
#             starts = [t.start for t in tokens[file]]
#             start_cache[file] = starts
#         return bisect.bisect_left(starts, start)
#
#     new_spans = {}
#     for group_id, spans in match.spans.items():
#         # if there exists an expanded group
#         # for which all current spans are contained
#         # in some expanded span, then skip this group
#         if any(all(any(span.file == other.file and \
#                        span.start >= other.start and \
#                        span.stop <= other.stop
#                        for other in expanded)
#                    for span in spans)
#                for expanded in new_spans.values()):
#             continue
#         # first, last index into file's tokens for each span
#         indices = {span: (get_index(span.file, span.start),
#                           get_index(span.file, span.stop) - 1)
#                    for span in spans}
#
#         while True:
#             changed = False
#             # find previous and next tokens for each span
#             prevs = set(tokens[span.file][first - 1].val if first > 0 else None
#                         for span, (first, last) in indices.items())
#             nexts = set((tokens[span.file][last + 1].val
#                          if last + 1 < len(tokens[span.file]) else None)
#                         for span, (first, last) in indices.items())
#
#             # expand front of spans
#             if len(prevs) == 1 and prevs.pop() is not None:
#                 changed = True
#                 indices = {span: (first - 1, last)
#                            for span, (first, last) in indices.items()}
#                 # expand back of spans
#             if len(nexts) == 1 and nexts.pop() is not None:
#                 changed = True
#                 indices = {span: (start, stop + 1)
#                            for span, (start, stop) in indices.items()}
#             if not changed:
#                 break
#
#         new_spans[group_id] = [Span(span.file,
#                                     tokens[span.file][first].start,
#                                     tokens[span.file][last].stop)
#                                for span, (first, last) in indices.items()]
#     return MatchResult(match.a, match.b, match.score, new_spans)
#
#
# def flatten_spans(matches):
#     """Return a pair of dicts mapping Files to lists of Fragments. Each
#     list of Fragments is the fragmented contents of an entire file.
#
#     match - a dict mapping pass IDs to MatchResults
#     """
#     # separate spans by submission
#     a_spans = {}
#     b_spans = {}
#     for pass_id, match in matches.items():
#         for group, spans in match.spans.items():
#             for span in spans:
#                 if span.file.submission.id == match.a:
#                     spans = a_spans
#                 elif span.file.submission.id == match.b:
#                     spans = b_spans
#                 else:
#                     assert false, "Span from unknown submission in match"
#                 spans.setdefault(pass_id, {}) \
#                     .setdefault(group, []) \
#                     .append(span)
#
#     a_results = {}
#     b_results = {}
#     for spans, results in (a_spans, a_results), (b_spans, b_results):
#         # separate by file, move pass_id and group into tuple
#         by_file = {}
#         for pass_id, spans in spans.items():
#             for group, spans in spans.items():
#                 for span in spans:
#                     entry = by_file.setdefault(span.file, [])
#                     entry.append((span, pass_id, group))
#
#         for file, span_data in by_file.items():
#             # iterate through text, creating list of Fragments
#             file_results = []
#             span_data.sort(key=lambda s: s[0].start)
#             with open(File.query.get(file).full_path, "r") as f:
#                 text = f.read()
#             current_spans = []
#             current_text = []
#
#             def create_frag():
#                 groups = {}
#                 for span, pass_id, group in current_spans:
#                     groups.setdefault(pass_id, []).append(group)
#                     if "distro" in groups[pass_id]:
#                         groups[pass_id] = ["distro"]
#                 file_results.append(Fragment(groups, "".join(current_text)))
#
#             for i, c in enumerate(text):
#                 # calculate new current groups
#                 new_spans = [(span, pass_id, group)
#                              for span, pass_id, group in current_spans
#                              if span.stop > i]
#                 while span_data and span_data[0][0].start == i:
#                     new_spans.append(span_data.pop(0))
#
#                 # emit fragment if span would end or start
#                 if new_spans != current_spans:
#                     create_frag()
#                     current_text = []
#                 current_spans = new_spans
#                 current_text.append(c)
#
#             # final fragment, possibly empty
#             create_frag()
#             results[file] = file_results
#
#     return a_results, b_results
