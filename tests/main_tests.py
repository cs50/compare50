import unittest
import tempfile
import os
import io
from unittest.mock import patch
import compare50.__main__ as main
import compare50._api as api

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
        api.progress_bar("foo", disable=True).__enter__()

    def tearDown(self):
        super().tearDown()
        api._progress_bar.close()
        api._progress_bar = None

    def test_no_submissions(self):
        preprocessor = lambda tokens : tokens
        os.mkdir("foo")
        subs = self.factory.get_all(["foo"], preprocessor)
        subs = {sub for sub in subs if sub.files}
        self.assertEqual(subs, set())

    def test_one_submission(self):
        preprocessor = lambda tokens : tokens
        os.mkdir("foo")
        os.mkdir("foo/bar")
        with open("foo/bar/baz.txt", "w") as f:
            pass

        subs = list(self.factory.get_all(["foo"], preprocessor))
        subs = [sub for sub in subs if sub.files]
        self.assertEqual(len(subs), 1)
        self.assertEqual(subs[0].path.name, "foo")

        subs = list(self.factory.get_all(["foo/bar"], preprocessor))
        subs = [sub for sub in subs if sub.files]
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
        subs = [sub for sub in subs if sub.files]
        self.assertEqual(subs[0].preprocessor(""), ["foo"])

    def test_single_file_submission(self):
        preprocessor = lambda tokens : tokens
        os.mkdir("foo")
        with open("foo/bar.py", "w") as f:
            pass

        subs = list(self.factory.get_all(["foo/bar.py"], preprocessor))
        subs = [sub for sub in subs if sub.files]
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
        subs = {sub for sub in subs if sub.files}
        self.assertEqual(subs, set())

    def test_include_pattern(self):
        preprocessor = lambda tokens : tokens
        os.mkdir("foo")
        with open("foo/bar.py", "w") as f:
            pass

        self.factory.exclude("*")
        self.factory.include("bar.py")
        subs = list(self.factory.get_all(["foo"], preprocessor))
        subs = [sub for sub in subs if sub.files]
        self.assertEqual(len(subs), 1)
        self.assertEqual(len(list(subs[0].files)), 1)
        self.assertEqual(str(list(subs[0].files)[0].name), "bar.py")

    def test_ignore_non_utf8(self):
        preprocessor = lambda tokens : tokens
        os.mkdir("foo")
        with open("foo/bar.py", "wb") as f:
            f.write(b'\x80abc')

        subs = self.factory.get_all(["foo"], preprocessor)
        subs = {sub for sub in subs if sub.files}
        self.assertEqual(subs, set())

    def test_permission_error(self):
        os.mkdir("foo")
        file_path = "foo/bar.py"
        with open(file_path, "w") as f:
            f.write("test content")
        os.chmod(file_path, 0o000)
        with self.assertRaises(PermissionError):
            main.SubmissionFactory._is_valid_utf8(file_path)
        os.chmod(file_path, 0o644)
    
    def test_excepthook_permission_error(self):
        error = PermissionError("Permission denied")
        error.filename = "/path/to/restricted/file.py"
        with patch('sys.stderr', new_callable=io.StringIO) as mock_stderr:
            with patch('sys.exit') as mock_exit:
                main.excepthook(PermissionError, error, None)
                error_output = mock_stderr.getvalue()
                self.assertIn("Permission denied: /path/to/restricted/file.py", error_output)
                mock_exit.assert_called_once_with(1)


if __name__ == "__main__":
    unittest.main()
