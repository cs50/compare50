import unittest
import tempfile
import os
import sys

from compare50.__main__ import Preprocessor
import compare50.comparators.winnowing as winnowing
import compare50.data as data

class TestCase(unittest.TestCase):
    def setUp(self):
        self.working_directory = tempfile.TemporaryDirectory()
        self._wd = os.getcwd()
        os.chdir(self.working_directory.name)

    def tearDown(self):
        self.working_directory.cleanup()
        os.chdir(self._wd)

class TestIgnore(TestCase):
    def setUp(self):
        super().setUp()
        self.content = "def bar():\n"\
                       "    print('qux')\n"

        with open("foo.py", "w") as f:
            f.write(self.content)

        self.file = data.Submission(".", ["foo.py"]).files[0]

    def test_no_ignore(self):
        tokens = list(self.file.tokens())
        ignored_index = winnowing.Index(k=2, t=3, complete=True)
        relevant_tokens = winnowing.ignore(self.file, ignored_index, tokens=tokens)
        self.assertEqual(relevant_tokens, tokens)

    def test_ignore_all(self):
        tokens = list(self.file.tokens())
        ignored_index = winnowing.Index(k=2, t=3, complete=True)
        ignored_index.include(self.file, tokens=tokens)
        relevant_tokens = winnowing.ignore(self.file, ignored_index, tokens=tokens)
        self.assertEqual(relevant_tokens, [])

    def test_ignore_half(self):
        ignore_content = self.content.split("\n")[0]
        with open("ignore.py", "w") as f:
            f.write(ignore_content)
        ignored_file = data.Submission(".", ["ignore.py"]).files[0]
        ignored_index = winnowing.Index(k=2, t=3, complete=True)
        ignored_index.include(ignored_file)

        relevant_tokens = winnowing.ignore(self.file, ignored_index)

        end = list(ignored_file.tokens())[-1].end
        expected_tokens = [t for t in self.file.tokens() if t.start >= end]

        self.assertEqual(relevant_tokens, expected_tokens)


if __name__ == "__main__":
    suite = unittest.TestLoader().loadTestsFromModule(sys.modules[__name__])
    unittest.TextTestRunner(verbosity=2).run(suite)
