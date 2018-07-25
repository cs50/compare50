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
    def test_fragmentize_single_span(self):
        content = "0123456789"
        filename = "foo.txt"
        with open(filename, "w") as f:
            f.write(content)

        file = list(data.Submission.from_file_path(pathlib.Path(filename), lambda ts: ts).files())[0]
        span = data.Span(file, 3, 5)
        fragments = renderer.fragmentize(file, [span])
        self.assertEqual([f.content for f in fragments], ["012", "34", "56789"])
        self.assertEqual(fragments[0].spans, set())
        self.assertEqual(fragments[1].spans, {span})
        self.assertEqual(fragments[2].spans, set())
