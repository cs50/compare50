import unittest
import tempfile
import zipfile
import os
import compare50.__main__ as main

class TestCase(unittest.TestCase):
    def setUp(self):
        self.working_directory = tempfile.TemporaryDirectory()
        self._wd = os.getcwd()
        os.chdir(self.working_directory.name)

    def tearDown(self):
        self.working_directory.cleanup()
        os.chdir(self._wd)


class TestSubmissionFactory(TestCase):
    def setUp(self):
        super().setUp()
        self.factory = main.SubmissionFactory()

    def tearDown(self):
        super().tearDown()

    def test_no_submissions(self):
        preprocessor = lambda tokens : tokens
        os.mkdir("foo")
        subs = self.factory.get_all(["foo"], preprocessor)
        self.assertEqual(subs, set())

    def test_one_submission(self):
        preprocessor = lambda tokens : tokens
        os.mkdir("foo")
        os.mkdir("foo/bar")
        with open("foo/bar/baz.txt", "w") as f:
            pass

        subs = list(self.factory.get_all(["foo"], preprocessor))
        self.assertEqual(len(subs), 1)
        self.assertEqual(subs[0].path.name, "foo")

        subs = list(self.factory.get_all(["foo/bar"], preprocessor))
        self.assertEqual(len(subs), 1)
        self.assertEqual(subs[0].path.parent.name, "foo")
        self.assertEqual(subs[0].path.name, "bar")

    def test_preprocessor_is_passed(self):
        preprocessor = lambda tokens: list(tokens) + ["foo"]
        os.mkdir("foo")
        os.mkdir("foo/bar")
        with open("foo/bar/baz.txt", "w") as f:
            pass

        subs = list(self.factory.get_all(["foo"], preprocessor))
        self.assertEqual(subs[0].preprocessor(""), ["foo"])

    def test_single_file_submission(self):
        preprocessor = lambda tokens : tokens
        os.mkdir("foo")
        with open("foo/bar.py", "w") as f:
            pass

        subs = list(self.factory.get_all(["foo/bar.py"], preprocessor))
        self.assertEqual(len(subs), 1)
        self.assertEqual(len(list(subs[0].files)), 1)
        self.assertEqual(str(list(subs[0].files)[0].name), "bar.py")

    def test_exclude_pattern(self):
        preprocessor = lambda tokens : tokens
        os.mkdir("foo")
        with open("foo/bar.py", "w") as f:
            pass

        self.factory.exclude("*")
        subs = self.factory.get_all(["foo"], preprocessor)
        self.assertEquals(subs, set())

    def test_include_pattern(self):
        preprocessor = lambda tokens : tokens
        os.mkdir("foo")
        with open("foo/bar.py", "w") as f:
            pass

        self.factory.exclude("*")
        self.factory.include("bar.py")
        subs = list(self.factory.get_all(["foo"], preprocessor))
        self.assertEqual(len(subs), 1)
        self.assertEqual(len(list(subs[0].files)), 1)
        self.assertEqual(str(list(subs[0].files)[0].name), "bar.py")

    def test_ignore_non_utf8(self):
        preprocessor = lambda tokens : tokens
        os.mkdir("foo")
        with open("foo/bar.py", "wb") as f:
            f.write(b'\x80abc')

        subs = self.factory.get_all(["foo"], preprocessor)
        self.assertEqual(subs, set())


if __name__ == "__main__":
    unittest.main()
