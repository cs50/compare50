import collections
import concurrent.futures as futures
import heapq
import os
import pathlib

from .data import *

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
    span_matches.expand()
    return span_matches

def create_groups(submission_matches, comparator, ignored_files):
    file_matches = [fm for sm in submission_matches for fm in sm.file_matches]

    sub_match_to_span_matches = collections.defaultdict(list)
    span_matches_list = list(comparator.create_spans(file_matches, ignored_files))

    groups = []
    # for span_matches in map(_expand, span_matches_list):
        # sub_match_to_span_matches[(span_matches.file_a.submission.id, span_matches.file_b.submission.id)].append(span_matches)

    # for gs in map(group_spans, sub_match_to_span_matches.values()):
        # groups.extend(gs)
    with futures.ProcessPoolExecutor() as executor:
        for span_matches in executor.map(_expand, span_matches_list):
            sub_match_to_span_matches[(span_matches.file_a.submission.id, span_matches.file_b.submission.id)].append(span_matches)

        for gs in executor.map(group_spans, sub_match_to_span_matches.values()):
            groups.extend(gs)

    subs_to_groups = collections.defaultdict(list)

    for group in groups:
        subs_to_groups[(group.sub_a, group.sub_b)].append(group)

    return [(sm.sub_a, sm.sub_b, subs_to_groups[(sm.sub_a, sm.sub_b)]) for sm in submission_matches]


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

    return _filter_subsumed_groups([Group(spans) for spans in content_to_spans.values()])


def _is_span_subsumed(span, other_spans):
    for other_span in other_spans:
        if span.start >= other_span.start and span.end <= other_span.end:
            return True
    return False


def _is_group_subsumed(group, groups):
    for other_group in groups:
        if other_group == group or len(other_group.spans) < len(group.spans):
            continue

        for span in group.spans:
            if not _is_span_subsumed(span, other_group.spans):
                break
        else:
            return True
    return False


def _filter_subsumed_groups(groups):
    return [g for g in groups if not _is_group_subsumed(g, groups)]


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

    #
    #
    # class HTMLFile:
    #     def __init__(self):
    #         self.map = collections.OrderedDict()
    #         self._span_to_content = collections.OrderedDict()
    #
    #     def add_pre(self):
    #         pass
    #
    #     def add_post(self):
    #         pass
    #
    #     def add_span(self, span):
    #         left_i = 0
    #         while not span.start - left_i in self.map:
    #             left_i -= 1
    #
    #         right_i = 0
    #         while not span.end + right_i in self.map:
    #             right_i += 1
    #
    #         content = []
    #         for i in range(span.start - left_i, span.end + right_i + 1):
    #             if i in self.map:
    #                 content.append(self.map[i])
    #
    #         self._span_to_content[span] = content
    #         return content
    #
    #     def add(self, index, data):
    #         self.map[index] = data
    #
    #     def construct(self):
    #         code = []
    #         for content in self.map.values():
    #             code.append(content)
    #         return "\n".join(code)
    #
    #
    # class PygmentsParser(HTMLParser):
    #     def __init__(self, *args, **kwargs):
    #         super().__init__(*args, **kwargs)
    #         self.count = 0
    #         self.is_counting = False
    #         self.spans = tuple()
    #         self.html_file = None
    #
    #         self._tag = None
    #         self._attrs = None
    #
    #     def handle_starttag(self, tag, attrs):
    #         if tag == "pre":
    #             self.is_counting = True
    #             self._tag = tag
    #             self._attrs = attrs
    #         #print("Encountered a start tag:", tag, attrs)
    #
    #     def handle_endtag(self, tag):
    #         if tag == "pre":
    #             self.is_counting = False
    #         #print("Encountered an end tag :", tag)
    #
    #     def handle_data(self, data):
    #         #print("Encountered some data: {} - {}".format(self.count, data))
    #         if not self.is_counting:
    #             return
    #
    #         formatted_attrs = []
    #         for attr in self._attrs:
    #             formatted_attrs.append(f"{attr}={self._attrs[attr]}")
    #
    #         self.html_file.add(self.count, f"<{self._tag} {' '.join(formatted_attrs)}> {data} </{self._tag}>")
    #         self.count += len(data)
    #
    #     def start(self, content, spans):
    #         self.spans = spans
    #         self.html_file = HTMLFile()
    #         self.feed(content)
    #         return self.html_file
