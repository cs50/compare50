import collections
import heapq
import itertools

import intervaltree

import concurrent.futures
from .data import SubmissionMatch, Submission, Span, SpanMatch, Group, BisectList

__all__ = ["rank_submissions", "create_groups", "missing_spans", "expand"]


def rank_submissions(submissions, archive_submissions, ignored_files, comparator, n=50):
    """Rank all submissions, take the top n."""
    submission_matches = comparator.score(submissions, archive_submissions, ignored_files)

    # Keep only top `n` submission matches
    return heapq.nlargest(n, submission_matches, lambda sub_match : sub_match.score)


def create_groups(submission_matches, ignored_files, comparator):
    """Find all shared groups between submission_matches."""
    missing_spans_cache = {}
    sub_match_to_ignored_spans = {}
    sub_match_to_groups = {}

    for span_matches, ignored_spans in comparator.compare(submission_matches, ignored_files):
        if not span_matches:
            continue

        sub_a = span_matches[0].span_a.file.submission
        sub_b = span_matches[0].span_b.file.submission

        new_ignored_spans = []
        for sub in (sub_a, sub_b):
            for file in sub.files:
                # Divide ignored_spans per file
                ignored_spans_file = [span for span in ignored_spans if span.file==file]

                # Find all spans lost by preprocessors for file_a
                if file not in missing_spans_cache:
                    missing_spans_cache[file] = missing_spans(file)
                ignored_spans_file.extend(missing_spans_cache[file])

                # Flatten the spans (they could be overlapping)
                new_ignored_spans += _flatten_spans(ignored_spans_file)

        sub_match_to_ignored_spans[(sub_a, sub_b)] = new_ignored_spans
        sub_match_to_groups[(sub_a, sub_b)] = _group_span_matches(span_matches)

    return [(sm.sub_a,
             sm.sub_b,
             sub_match_to_groups[(sm.sub_a, sm.sub_b)],
             sub_match_to_ignored_spans[(sm.sub_a, sm.sub_b)])
            for sm in submission_matches]


def missing_spans(file, original_tokens=None, preprocessed_tokens=None):
    """
    Find which spans were not part of tokens (due to a preprocessor stripping them).
    """
    if original_tokens is None:
        original_tokens = file.unprocessed_tokens()
    if preprocessed_tokens is None:
        preprocessed_tokens = list(file.submission.preprocessor(original_tokens))

    if not original_tokens:
        return []

    file_start = original_tokens[0].start
    file_end = original_tokens[-1].end

    spans = []
    start = file_start
    for token in preprocessed_tokens:
        if token.start != start:
            spans.append(Span(file, start, token.start))
        start = token.end

    if start < file_end:
        spans.append(Span(file, start, file_end))

    return spans


def expand(span_matches, tokens_a, tokens_b):
    """
    Expand all span matches.
    returns a new instance of SpanMatches with maximally extended spans.
    """
    if not span_matches:
        return span_matches

    # expanded_span_matches = intervaltree.IntervalTree()
    expanded_span_matches = set()

    tokens_a = BisectList.from_sorted(tokens_a, key=lambda tok: tok.start)
    tokens_b = BisectList.from_sorted(tokens_b, key=lambda tok: tok.start)

    span_tree_a = intervaltree.IntervalTree()
    span_tree_b = intervaltree.IntervalTree()

    def is_subsumed(span, tree):
        """ Determine if span is strictly smaller than any interval in tree.
        Assumes that tree contains no intersecting intervals"""
        intervals = tree[span.start:span.end]
        for interval in intervals:
            if span.start >= interval.begin and span.end <= interval.end:
                return True
        return False

    for span_a, span_b in span_matches:
        if is_subsumed(span_a, span_tree_a) and is_subsumed(span_b, span_tree_b):
            continue

        # Expand left
        start_a = tokens_a.bisect_key_right(span_a.start) - 2
        start_b = tokens_b.bisect_key_right(span_b.start) - 2
        while min(start_a, start_b) >= 0 and tokens_a[start_a] == tokens_b[start_b]:
            start_a -= 1
            start_b -= 1
        start_a += 1
        start_b += 1

        # Expand right
        end_a = tokens_a.bisect_key_right(span_a.end) - 2
        end_b = tokens_b.bisect_key_right(span_b.end) - 2
        try:
            while tokens_a[end_a] == tokens_b[end_b]:
                end_a += 1
                end_b += 1
        except IndexError:
            pass
        end_a -= 1
        end_b -= 1

        new_span_a = Span(span_a.file, tokens_a[start_a].start, tokens_a[end_a].end)
        new_span_b = Span(span_b.file, tokens_b[start_b].start, tokens_b[end_b].end)

        span_tree_a.addi(new_span_a.start, new_span_a.end)
        span_tree_b.addi(new_span_b.start, new_span_b.end)

        # Add new spans
        expanded_span_matches.add(SpanMatch(new_span_a, new_span_b))

    return list(expanded_span_matches)


def _flatten_spans(spans):
    """
    Flatten a collection of spans.
    The resulting list of spans covers the same area and has no overlapping spans.
    """
    if len(spans) <= 1:
        return spans

    spans = sorted(spans, key=lambda span: span.start)
    file = spans[0].file

    flattened_spans = []
    start = spans[0].start
    cur = spans[0]
    for i in range(len(spans) - 1):
        next = spans[i + 1]
        if cur.end < next.start:
            flattened_spans.append(Span(file, start, cur.end))
            start = next.start
        if cur.end <= next.end:
            cur = next

    flattened_spans.append(Span(file, start, cur.end))
    return flattened_spans


def _group_span_matches(span_matches):
    """
    Transforms a list of SpanMatch into a list of Groups.
    Finds all spans that share the same content, and groups them in one Group.
    returns a list of Groups.
    """
    span_groups = _transitive_closure(span_matches)
    return _filter_subsumed_groups([Group(spans) for spans in span_groups])


def _transitive_closure(connections):
    class Graph:
        def __init__(self):
            self.connections = collections.defaultdict(set)

        def add(self, a, b):
            self.connections[a].add(b)
            self.connections[b].add(a)

        def traverse(self, node, visited=None):
            if visited is None:
                visited = set()

            visited.add(node)

            for other_node in self.connections[node]:
                if other_node not in visited:
                    self.traverse(other_node, visited)

            return visited

    graph = Graph()
    for a, b in connections:
        graph.add(a, b)

    trans_closure = []
    nodes = graph.connections.keys()
    while nodes:
        node = next(iter(nodes))
        reachable_nodes = graph.traverse(node)
        nodes -= reachable_nodes
        trans_closure.append(reachable_nodes)
    return trans_closure


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
            if not _is_span_subsumed(span, filter(lambda other: span.file == other.file, other_group.spans)):
                break
        else:
            return True
    return False


def _filter_subsumed_groups(groups):
    return [g for g in groups if not _is_group_subsumed(g, groups)]


# TODO: remove before we ship
class FauxExecutor:
    class FauxFuture:
        def __init__(self, result=None, exception=None):
            self._result = result
            self._exception = exception

        def cancel(self):
            return False

        def cancelled(self):
            return False

        def running(self):
            return False

        def result(self, timeout=None):
            if self._exception is not None:
                raise self._exception
            return self._result

        def exception(self, timeout=None):
            return self._exception

        def add_done_callback(fn):
            fn()

    def __init__(self, *_args, **_kwargs):
        pass

    def map(self, fn, *iterables, **_kwargs):
        for iterable in iterables:
            for res in map(fn, iterable):
                yield res

    def submit(self, fn, *args, **kwargs):
        try:
            result = fn(*args, **kwargs)
        except BaseException as e:
            return self.FauxFuture(exception=e)
        else:
            return self.FauxFuture(result=result)



    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        return


# TODO: Remove before we ship
Executor = concurrent.futures.ProcessPoolExecutor


