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

def create_groups(submission_matches, comparator, ignored_files):
    file_matches = [fm for sm in submission_matches for fm in sm.file_matches]

    sub_match_to_span_matches = collections.defaultdict(list)
    matches_list = list(comparator.create_spans(file_matches, ignored_files))

    for span_matches, ignored_spans in matches_list:
        sub_match_to_span_matches[(span_matches.file_a.submission,
                                   span_matches.file_b.submission)].append(span_matches)

    groups = []
    for grouped_spans in (group_spans(span_matches) for span_matches in sub_match_to_span_matches.values()):
        groups.extend(grouped_spans)

    sub_match_to_groups = collections.defaultdict(list)
    for group in groups:
        sub_match_to_groups[(group.sub_a, group.sub_b)].append(group)

    return [(sm.sub_a, sm.sub_b, sub_match_to_groups[(sm.sub_a, sm.sub_b)]) for sm in submission_matches]


def group_spans(span_matches_list):
    """
    Transforms a list of SpanMatches into a list of Groups.
    Finds all spans that share the same content, and groups them in one Group.
    returns a list of Groups.
    """
    span_groups = transitive_closure([(span_a, span_b) for span_matches in span_matches_list for span_a, span_b in span_matches])
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
