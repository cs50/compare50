import unittest
import tempfile
import os

from compare50.__main__ import Preprocessor
import compare50._data as data
import compare50._api as api

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
        span_matches = []
        spans = [self.span(i) for i in range(11)]
        for i in range(10):
            span_matches.append((spans[i], spans[i + 1]))

        groups = api._group_span_matches(span_matches)
        groups = list(groups)
        self.assertEqual(list(groups), [data.Group(spans)])

    def test_single_group(self):
        # Generate matches (0,1) (1,2) ... (9,10)
        span_matches = []
        spans_1 = [self.span(i) for i in range(11)]
        for i in range(10):
            span_matches.append((spans_1[i], spans_1[i + 1]))

        # Generate matches (10,11) (11,12) ... (19,20)
        spans_2 = [self.span(10 + i) for i in range(11)]
        for i in range(10):
            span_matches.append((spans_2[i], spans_2[i + 1]))

        groups = api._group_span_matches(span_matches)
        self.assertEqual(list(groups), [data.Group(spans_1 + spans_2)])

    def test_multiple_spanmatches_multiple_groups(self):
        # Generate matches (0,1) (1,2) ... (9,10)
        span_matches = []
        spans_1 = [self.span(i) for i in range(11)]
        for i in range(10):
            span_matches.append((spans_1[i], spans_1[i + 1]))

        # Generate matches (11,12) (12,13) ... (20,21)
        spans_2 = [self.span(11 + i) for i in range(11)]
        for i in range(10):
            span_matches.append((spans_2[i], spans_2[i + 1]))

        groups = api._group_span_matches(span_matches)
        self.assertEqual(set(groups), {data.Group(spans_1), data.Group(spans_2)})


class TestFlatten(unittest.TestCase):
    def span(self, start, end):
        file = data.Submission(".", ["bar/foo"]).files[0]
        return data.Span(file, start, end)

    def test_flatten_spans_no_spans(self):
        self.assertEqual(api._flatten_spans([]), [])

    def test_flatten_spans_one_span(self):
        span = self.span(0, 10)
        self.assertEqual(api._flatten_spans([span]), [span])

    def test_flatten_spans_overlapping_spans(self):
        span_1 = self.span(0, 10)
        span_2 = self.span(5, 15)
        resulting_span = self.span(0, 15)
        self.assertEqual(api._flatten_spans([span_1, span_2]), [resulting_span])

    def test_connecting_spans(self):
        span_1 = self.span(0, 10)
        span_2 = self.span(10, 20)
        resulting_span = self.span(0, 20)
        self.assertEqual(api._flatten_spans([span_1, span_2]), [resulting_span])

        span_1 = self.span(0, 9)
        span_2 = self.span(10, 20)
        self.assertEqual(api._flatten_spans([span_1, span_2]), [span_1, span_2])

    def test_subsuming_spans(self):
        span_1 = self.span(0, 30)
        span_2 = self.span(10, 20)
        resulting_span = self.span(0, 30)
        self.assertEqual(api._flatten_spans([span_1, span_2]), [resulting_span])

        span_1 = self.span(0, 30)
        span_2 = self.span(10, 40)
        resulting_span = self.span(0, 40)
        self.assertEqual(api._flatten_spans([span_1, span_2]), [resulting_span])


class TestMissingSpans(unittest.TestCase):
    def setUp(self):
        self.working_directory = tempfile.TemporaryDirectory()
        self._wd = os.getcwd()
        os.chdir(self.working_directory.name)

        self.content = "def bar():\n"\
                       "    print('qux')\n"

        with open("foo.py", "w") as f:
            f.write(self.content)

        self.file = data.Submission(".", ["foo.py"]).files[0]

    def tearDown(self):
        self.working_directory.cleanup()
        os.chdir(self._wd)

    def span(self, start, end):
        return data.Span(self.file, start, end)

    def test_all_spans_missing(self):
        self.file = data.Submission(".", ["foo.py"], preprocessor=lambda tokens : []).files[0]
        resulting_span = self.span(0, len(self.content))
        spans = api.missing_spans(self.file)
        self.assertEqual(spans, [resulting_span])

    def test_last_span_missing(self):
        missing_tokens = []
        def preprocessor(tokens):
            missing_tokens.append(tokens[-1])
            return tokens[:-1]

        self.file = data.Submission(".", ["foo.py"], preprocessor=preprocessor).files[0]
        spans = api.missing_spans(self.file)
        resulting_span = self.span(missing_tokens[0].start, len(self.content))
        self.assertEqual(spans, [resulting_span])

    def test_first_span_missing(self):
        missing_tokens = []
        def preprocessor(tokens):
            missing_tokens.append(tokens[0])
            return tokens[1:]

        self.file = data.Submission(".", ["foo.py"], preprocessor=preprocessor).files[0]
        spans = api.missing_spans(self.file)
        resulting_span = self.span(0, missing_tokens[0].end)
        self.assertEqual(spans, [resulting_span])

    def test_middle_span_missing(self):
        missing_tokens = []
        def preprocessor(tokens):
            middle = len(tokens) // 2
            missing_tokens.append(tokens[middle])
            return tokens[:middle] + tokens[middle + 1:]

        self.file = data.Submission(".", ["foo.py"], preprocessor=preprocessor).files[0]
        spans = api.missing_spans(self.file)
        resulting_span = self.span(missing_tokens[0].start, missing_tokens[0].end)
        self.assertEqual(spans, [resulting_span])


if __name__ == '__main__':
    unittest.main()
