import unittest
import tempfile
import os
import sys

from compare50.__main__ import Preprocessor
import compare50.comparators._winnowing as winnowing
import compare50._data as data

class TestCase(unittest.TestCase):
    def setUp(self):
        self.working_directory = tempfile.TemporaryDirectory()
        self._wd = os.getcwd()
        os.chdir(self.working_directory.name)

    def tearDown(self):
        self.working_directory.cleanup()
        os.chdir(self._wd)

class TestCompareIndexIgnoreTokens(TestCase):
    def setUp(self):
        super().setUp()
        self.content = "def bar():\n"\
                       "    print('qux')\n"

        with open("foo.py", "w") as f:
            f.write(self.content)

        self.file = data.Submission(".", ["foo.py"]).files[0]

    def test_no_ignore(self):
        tokens = list(self.file.tokens())
        ignored_index = winnowing.CompareIndex(k=2)
        relevant_token_lists = ignored_index.unignored_tokens(self.file, tokens=tokens)
        self.assertEqual(len(relevant_token_lists), 1)
        self.assertEqual(relevant_token_lists[0], tokens)

    def test_ignore_all(self):
        tokens = list(self.file.tokens())
        ignored_index = winnowing.CompareIndex(k=2)
        ignored_index.include(self.file, tokens=tokens)
        relevant_token_lists = ignored_index.unignored_tokens(self.file, tokens=tokens)
        self.assertEqual(relevant_token_lists, [])

    def test_ignore_half(self):
        ignore_content = self.content.split("\n")[0]
        with open("ignore.py", "w") as f:
            f.write(ignore_content)
        ignored_file = data.Submission(".", ["ignore.py"]).files[0]
        ignored_index = winnowing.CompareIndex(k=2)
        ignored_index.include(ignored_file)

        relevant_token_lists = ignored_index.unignored_tokens(self.file)

        end = list(ignored_file.tokens())[-1].end
        expected_tokens = [t for t in self.file.tokens() if t.start >= end]

        self.assertEqual(len(relevant_token_lists), 1)
        self.assertEqual(relevant_token_lists[0], expected_tokens)


if __name__ == "__main__":
    suite = unittest.TestLoader().loadTestsFromModule(sys.modules[__name__])
    unittest.TextTestRunner(verbosity=2).run(suite)
