import unittest
import tempfile
import os
import pathlib
import compare50.html_renderer as renderer
import compare50.data as data

class TestCase(unittest.TestCase):
    def setUp(self):
        self.working_directory = tempfile.TemporaryDirectory()
        self._wd = os.getcwd()
        os.chdir(self.working_directory.name)

    def tearDown(self):
        self.working_directory.cleanup()
        os.chdir(self._wd)

class TestFragmentize(TestCase):
    def setUp(self):
        super().setUp()
        self.content = "0123456789"
        self.filename = "foo.txt"
        with open(self.filename, "w") as f:
            f.write(self.content)

        self.file = list(data.Submission.from_file_path(pathlib.Path(self.filename), lambda ts: ts).files())[0]

    def test_single_span(self):
        span = data.Span(self.file, 3, 5)
        fragments = renderer.fragmentize(self.file, [span])
        self.assertEqual([f.content for f in fragments], [("012",), ("34",), ("56789",)])
        self.assertEqual(fragments[0].spans, tuple())
        self.assertEqual(fragments[1].spans, (span,))
        self.assertEqual(fragments[2].spans, tuple())

    def test_multiple_spans(self):
        span_1 = data.Span(self.file, 3, 5)
        span_2 = data.Span(self.file, 7, 9)
        fragments = renderer.fragmentize(self.file, [span_1, span_2])
        self.assertEqual([f.content for f in fragments], [("012",), ("34",), ("56",), ("78",), ("9",)])
        self.assertEqual(fragments[0].spans, tuple())
        self.assertEqual(fragments[1].spans, (span_1,))
        self.assertEqual(fragments[2].spans, tuple())
        self.assertEqual(fragments[3].spans, (span_2,))
        self.assertEqual(fragments[4].spans, tuple())

    def test_overlapping_spans(self):
        span_1 = data.Span(self.file, 3, 7)
        span_2 = data.Span(self.file, 5, 9)
        fragments = renderer.fragmentize(self.file, [span_1, span_2])
        self.assertEqual([f.content for f in fragments], [("012",), ("34",), ("56",), ("78",), ("9",)])
        self.assertEqual(fragments[0].spans, tuple())
        self.assertEqual(fragments[1].spans, (span_1,))
        self.assertEqual(set(fragments[2].spans), {span_1, span_2})
        self.assertEqual(fragments[3].spans, (span_2,))
        self.assertEqual(fragments[4].spans, tuple())

    def test_completely_overlapping_spans(self):
        span_1 = data.Span(self.file, 1, 9)
        span_2 = data.Span(self.file, 4, 6)
        fragments = renderer.fragmentize(self.file, [span_1, span_2])
        self.assertEqual([f.content for f in fragments], [("0",), ("123",), ("45",), ("678",), ("9",)])
        self.assertEqual(fragments[0].spans, tuple())
        self.assertEqual(fragments[1].spans, (span_1,))
        self.assertEqual(set(fragments[2].spans), {span_1, span_2})
        self.assertEqual(fragments[3].spans, (span_1,))
        self.assertEqual(fragments[4].spans, tuple())

    def test_from_start(self):
        span = data.Span(self.file, 0, 5)
        fragments = renderer.fragmentize(self.file, [span])
        self.assertEqual([f.content for f in fragments], [("01234",), ("56789",)])
        self.assertEqual(fragments[0].spans, (span,))
        self.assertEqual(fragments[1].spans, tuple())

    def test_till_end(self):
        span = data.Span(self.file, 5, len(self.content))
        fragments = renderer.fragmentize(self.file, [span])
        self.assertEqual([f.content for f in fragments], [("01234",), ("56789",)])
        self.assertEqual(fragments[0].spans, tuple())
        self.assertEqual(fragments[1].spans, (span,))

    def test_from_start_till_end(self):
        span = data.Span(self.file, 0, len(self.content))
        fragments = renderer.fragmentize(self.file, [span])
        self.assertEqual([f.content for f in fragments], [("0123456789",)])
        self.assertEqual(fragments[0].spans, (span,))

    def test_touching_spans(self):
        span_1 = data.Span(self.file, 3, 5)
        span_2 = data.Span(self.file, 5, 7)
        fragments = renderer.fragmentize(self.file, [span_1, span_2])
        self.assertEqual([f.content for f in fragments], [("012",), ("34",), ("56",), ("789",)])
        self.assertEqual(fragments[0].spans, tuple())
        self.assertEqual(fragments[1].spans, (span_1,))
        self.assertEqual(fragments[2].spans, (span_2,))
        self.assertEqual(fragments[3].spans, tuple())

    def test_spans_are_ordered(self):
        # Check that the spans are ordered by first opened
        span_1 = data.Span(self.file, 1, 9)
        span_2 = data.Span(self.file, 2, 8)
        span_3 = data.Span(self.file, 4, 6)
        fragments = renderer.fragmentize(self.file, [span_1, span_2, span_3])
        self.assertEqual([f.content for f in fragments], [("0",), ("1",), ("23",), ("45",), ("67",), ("8",), ("9",)])
        self.assertEqual(fragments[0].spans, tuple())
        self.assertEqual(fragments[1].spans, (span_1,))
        self.assertEqual(fragments[2].spans, (span_2, span_1))
        self.assertEqual(fragments[3].spans, (span_3, span_2, span_1))
        self.assertEqual(fragments[4].spans, (span_2, span_1))
        self.assertEqual(fragments[5].spans, (span_1,))
        self.assertEqual(fragments[6].spans, tuple())
