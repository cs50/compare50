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

    def test_fragmentize_single_span(self):
        span = data.Span(self.file, 3, 5)
        fragments = renderer.fragmentize(self.file, [span])
        self.assertEqual([f.content for f in fragments], ["012", "34", "56789"])
        self.assertEqual(fragments[0].spans, set())
        self.assertEqual(fragments[1].spans, {span})
        self.assertEqual(fragments[2].spans, set())

    def test_fragmentize_multiple_spans(self):
        span_1 = data.Span(self.file, 3, 5)
        span_2 = data.Span(self.file, 7, 9)
        fragments = renderer.fragmentize(self.file, [span_1, span_2])
        self.assertEqual([f.content for f in fragments], ["012", "34", "56", "78", "9"])
        self.assertEqual(fragments[0].spans, set())
        self.assertEqual(fragments[1].spans, {span_1})
        self.assertEqual(fragments[2].spans, set())
        self.assertEqual(fragments[3].spans, {span_2})
        self.assertEqual(fragments[4].spans, set())
