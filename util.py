import os

from backports.shutil_which import which
from tempfile import gettempdir, mkstemp
from werkzeug.utils import secure_filename

import patoolib


# Supported archives, per https://github.com/wummel/patool
ARCHIVES = [".bz2", ".tar", ".tar.gz", ".tgz", ".zip", ".7z", ".xz"]


# Supported helper applications
HELPERS = {
    "7z": [".7z"],
    "compress": [".z"],
    "unrar": [".rar"],
    "xz": [".xz"]
}


for progname, extensions in HELPERS.items():
    if which(progname):
        ARCHIVES.extend(extensions)


class NotFinishedException(Exception):
    """Raised when a valid request is made for results that are not yet ready"""
    pass


def save(file, dirpath):
    """Saves file at dirpath, extracting to identically named folder if archive."""
    filename = secure_filename(file.filename)
    path = os.path.join(dirpath, filename)
    if path.lower().endswith(tuple(ARCHIVES)):
        try:
            _, pathname = mkstemp(filename)
            file.save(pathname)
            os.mkdir(path)
            try:
                patoolib.extract_archive(pathname, outdir=path)
                print("Extracted!")
            except patoolib.util.PatoolError:
                abort(500) # TODO: pass helpful message
            os.remove(pathname)
        except Exception:
            abort(500) # TODO: pass helpful message
    else:
        file.save(path)


def ignored(path):
    """Returns whether the given path ends in an ignored name."""
    ignored_prefixes = [".", "__"]
    name = os.path.basename(path)
    return any(name.startswith(p) for p in ignored_prefixes)


def walk(directory):
    """Walks directory recursively, returning sorted list of paths of files therein."""
    files = []
    for (dirpath, dirnames, filenames) in os.walk(directory):
        if ignored(dirpath):
            continue
        for filename in filenames:
            if ignored(filename):
                continue
            files.append(os.path.join(dirpath, filename))
    sorted(sorted(files), key=str.upper)
    return files


def walk_submissions(directory):
    """Walks directory recursively, returning a list of submissions that are lists of files."""
    for (dirpath, dirnames, filenames) in os.walk(directory):
        if ignored(dirpath):
            continue
        dirnames = list(filter(lambda d: not ignored(d), dirnames))
        filenames = list(filter(lambda f: not ignored(f), filenames))
        if len(filenames) > 0:
            # single submission
            return [tuple(sorted([os.path.join(dirpath, f)
                                  for f in filenames]))]
        if len(dirnames) > 1:
            # multiple submissions, each in own subdirectory
            return [tuple(walk(os.path.join(dirpath, d))) for d in dirnames]


def submission_path(files):
    """Given a list of files in a submission, return the submission's path"""
    if len(files) == 1:
        return os.path.dirname(files[0])
    else:
        return os.path.commonpath(files)
