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


def create_groups(submission_matches, comparator, ignored_files):
    file_matches = [fm for sm in submission_matches for fm in sm.file_matches]

    sub_match_to_span_matches = collections.defaultdict(list)
    sub_match_to_ignored_spans = collections.defaultdict(list)

    missing_spans_cache = {}

    for span_matches, ignored_spans in comparator.create_spans(file_matches, ignored_files):
        if not span_matches:
            continue

        file_a = span_matches.file_a
        file_b = span_matches.file_b

        sub_match = (file_a.submission, file_b.submission)
        sub_match_to_span_matches[sub_match].append(span_matches)

        # Divide ignored_spans per file
        ignored_spans_a = []
        ignored_spans_b = []
        for span in ignored_spans:
            if span.file.id == file_a.id:
                ignored_spans_a.append(span)
            else:
                ignored_spans_b.append(span)

        # Find all spans lost by preprocessors for file_a
        if file_a not in missing_spans_cache:
            missing_spans_cache[file_a] = missing_spans(file_a)
        ignored_spans_a.extend(missing_spans_cache[file_a])

        # Find all spans lost by preprocessors for file_b
        if file_b not in missing_spans_cache:
            missing_spans_cache[file_b] = missing_spans(file_b)
        ignored_spans_b.extend(missing_spans_cache[file_b])

        # Flatten the spans (they could be overlapping)
        ignored_spans = flatten(ignored_spans_a) + flatten(ignored_spans_b)
        sub_match_to_ignored_spans[sub_match].extend(ignored_spans)

    groups = []
    for span_matches_list in sub_match_to_span_matches.values():
        span_pairs = [(span_a, span_b) for span_matches in span_matches_list for span_a, span_b in span_matches]
        groups.extend(group_span_pairs(span_pairs))

    sub_match_to_groups = collections.defaultdict(list)
    for group in groups:
        sub_match_to_groups[(group.sub_a, group.sub_b)].append(group)

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
        original_tokens = list(file.unprocessed_tokens())
    if preprocessed_tokens is None:
        preprocessed_tokens = list(file.submission.preprocessor(original_tokens))

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


def flatten(spans):
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


def group_span_pairs(span_pairs):
    """
    Transforms a list of span_pairs (2 item tuples of Spans) into a list of Groups.
    Finds all spans that share the same content, and groups them in one Group.
    returns a list of Groups.
    """
    span_groups = transitive_closure(span_pairs)
    return _filter_subsumed_groups([Group(spans) for spans in span_groups])


def transitive_closure(connections):
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
            if not _is_span_subsumed(span, other_group.spans):
                break
        else:
            return True
    return False


def _filter_subsumed_groups(groups):
    return [g for g in groups if not _is_group_subsumed(g, groups)]
