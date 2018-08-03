import unittest

from compare50.__main__ import Preprocessor
import compare50.data as data
import compare50.api as api

class TestCreateSpans(unittest.TestCase):
    pass


class TestRankSubmissions(unittest.TestCase):
    pass


class TestGroupSpans(unittest.TestCase):
    def span(self, start):
        file = data.Submission(".", ["bar/foo"]).files[0]
        return data.Span(file, start, start + 1)

    def test_single_spanmatches_single_group(self):
        # Generate matches (0,1) (1,2) ... (9,10)
        span_matches = data.SpanMatches()
        spans = [self.span(i) for i in range(11)]
        for i in range(10):
            span_matches.add(spans[i], spans[i + 1])

        groups = api.group_spans([span_matches])
        groups = list(groups)
        self.assertEqual(list(groups), [data.Group(spans)])

    def test_multiple_spanmatches_single_group(self):
        # Generate matches (0,1) (1,2) ... (9,10)
        span_matches_1 = data.SpanMatches()
        spans_1 = [self.span(i) for i in range(11)]
        for i in range(10):
            span_matches_1.add(spans_1[i], spans_1[i + 1])

        # Generate matches (10,11) (11,12) ... (19,20)
        span_matches_2 = data.SpanMatches()
        spans_2 = [self.span(10 + i) for i in range(11)]
        for i in range(10):
            span_matches_2.add(spans_2[i], spans_2[i + 1])

        groups = api.group_spans([span_matches_1, span_matches_2])
        self.assertEqual(list(groups), [data.Group(spans_1 + spans_2)])

    def test_multiple_spanmatches_multiple_groups(self):
        # Generate matches (0,1) (1,2) ... (9,10)
        span_matches_1 = data.SpanMatches()
        spans_1 = [self.span(i) for i in range(11)]
        for i in range(10):
            span_matches_1.add(spans_1[i], spans_1[i + 1])

        # Generate matches (11,12) (12,13) ... (20,21)
        span_matches_2 = data.SpanMatches()
        spans_2 = [self.span(11 + i) for i in range(11)]
        for i in range(10):
            span_matches_2.add(spans_2[i], spans_2[i + 1])

        groups = api.group_spans([span_matches_1, span_matches_2])
        self.assertEqual(set(groups), {data.Group(spans_1), data.Group(spans_2)})


class TestFlatten(unittest.TestCase):
    def span(self, start, end):
        file = data.Submission(".", ["bar/foo"]).files[0]
        return data.Span(file, start, end)

    def test_flatten_no_spans(self):
        self.assertEqual(api.flatten([]), [])

    def test_flatten_one_span(self):
        span = self.span(0, 10)
        self.assertEqual(api.flatten([span]), [span])

    def test_flatten_overlapping_spans(self):
        span_1 = self.span(0, 10)
        span_2 = self.span(5, 15)
        resulting_span = self.span(0, 15)
        self.assertEqual(api.flatten([span_1, span_2]), [resulting_span])

    def test_connecting_spans(self):
        span_1 = self.span(0, 10)
        span_2 = self.span(10, 20)
        resulting_span = self.span(0, 20)
        self.assertEqual(api.flatten([span_1, span_2]), [resulting_span])

        span_1 = self.span(0, 9)
        span_2 = self.span(10, 20)
        self.assertEqual(api.flatten([span_1, span_2]), [span_1, span_2])

if __name__ == '__main__':
    unittest.main()
