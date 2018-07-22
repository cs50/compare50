import unittest
import tempfile
import zipfile
import os
import compare50.__main__ as main
import compare50.errors
import compare50.data

def zipdir(name, dir):
    zip_file = zipfile.ZipFile(name, 'w', zipfile.ZIP_DEFLATED)
    _add_dir_to_zip(dir, zip_file)
    zip_file.close()

def _add_dir_to_zip(dir, zip_file):
    for root, dirs, files in os.walk(dir):
        for file in files:
            zip_file.write(os.path.join(root, file))

class TestCase(unittest.TestCase):
    def setUp(self):
        self.working_directory = tempfile.TemporaryDirectory()
        self._wd = os.getcwd()
        os.chdir(self.working_directory.name)

    def tearDown(self):
        self.working_directory.cleanup()
        os.chdir(self._wd)


class TestUnpack(TestCase):
    def setUp(self):
        self.working_directory = tempfile.TemporaryDirectory()
        self._wd = os.getcwd()
        os.chdir(self.working_directory.name)

    def tearDown(self):
        self.working_directory.cleanup()
        os.chdir(self._wd)

    def test_invalid_archive(self):
        with self.assertRaises(compare50.errors.Error):
            main.unpack("archive.foo", os.getcwd())

    def test_dest_does_not_exist(self):
        os.mkdir("foo")
        zipdir("bar.zip", "foo")
        with self.assertRaises(compare50.errors.Error):
            main.unpack("bar.zip", "baz")

    def test_empty_archive(self):
        os.mkdir("foo")
        zipdir("baz.zip", "foo")
        os.mkdir("bar")
        main.unpack("baz.zip", "bar")

        self.assertEqual(os.listdir("bar"), [])
        self.assertEqual(set(os.listdir(".")), {"foo", "bar", "baz.zip"})

    def test_non_empty_archive(self):
        os.mkdir("foo")
        with open("foo/foo_file1.txt", "w") as f:
            pass
        zipdir("baz.zip", "foo")
        os.mkdir("bar")
        main.unpack("baz.zip", "bar")

        self.assertEqual(os.listdir("bar"), ["foo"])
        self.assertEqual(os.listdir("bar/foo"), ["foo_file1.txt"])
        self.assertEqual(set(os.listdir(".")), {"foo", "bar", "baz.zip"})


class TestSubmissions(TestCase):
    def test_no_submissions(self):
        preprocessor = lambda tokens : tokens
        os.mkdir("foo")
        with main.submissions("foo", preprocessor) as subs:
            self.assertEqual(subs, [])

        zipdir("bar.zip", "foo")
        with main.submissions("bar.zip", preprocessor) as subs:
            self.assertEqual(subs, [])

    def test_one_submission(self):
        preprocessor = lambda tokens : tokens
        os.mkdir("foo")
        os.mkdir("foo/bar")
        with open("foo/bar/baz.txt", "w") as f:
            pass

        with main.submissions("foo", preprocessor) as subs:
            self.assertEqual(len(subs), 1)
            self.assertEqual(subs[0].path.name, "bar")

        os.chdir("foo")
        zipdir("baz.zip", "bar")
        with main.submissions("baz.zip", preprocessor) as subs:
            self.assertEqual(len(subs), 1)
            self.assertEqual(subs[0].path.name, "bar")

    def test_preprocessor_is_passed(self):
        preprocessor = lambda tokens: list(tokens) + ["foo"]
        os.mkdir("foo")
        os.mkdir("foo/bar")
        with open("foo/bar/baz.txt", "w") as f:
            pass

        with main.submissions("foo", preprocessor) as subs:
            self.assertEqual(subs[0].preprocessor(""), ["foo"])

    def test_ignores_files(self):
        preprocessor = lambda tokens : tokens
        os.mkdir("foo")
        os.mkdir("foo/bar")
        with open("foo/bar/baz.txt", "w") as f:
            pass

        with open("foo/qux.txt", "w") as f:
            pass

        with main.submissions("foo", preprocessor) as subs:
            self.assertEqual(len(subs), 1)
            self.assertEqual(subs[0].path.name, "bar")

        os.chdir("foo")
        zipdir("baz.zip", "bar")
        with main.submissions("baz.zip", preprocessor) as subs:
            self.assertEqual(len(subs), 1)
            self.assertEqual(subs[0].path.name, "bar")


class TestFiles(TestCase):
    pass

if __name__ == "__main__":
    unittest.main()
