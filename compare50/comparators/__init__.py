import pathlib

from ..data import Pass
from .. import preprocessors

from . import winnowing as _winnowing
from . import misspellings as _misspellings


class winnowing(Pass):
    """Removes all whitespace, normalizes all comments/ids/strings, and runs Winnowing with k=25, t=35."""

    preprocessors = [preprocessors.strip_whitespace,
                     preprocessors.strip_comments,
                     preprocessors.normalize_identifiers,
                     preprocessors.normalize_string_literals,
                     preprocessors.normalize_numeric_literals]
    comparator = _winnowing.Winnowing(k=25, t=35)


class winnowing_exact(Pass):
    """Only removes whitespace and runs Winnowing with k=25, t=35."""
    preprocessors = [preprocessors.strip_whitespace,
                     preprocessors.split_on_whitespace]
    comparator = _winnowing.Winnowing(k=25, t=35)


class misspellings(Pass):
    """Compares comments for identical English word misspellings."""

    preprocessors = [preprocessors.comments,
                     preprocessors.normalize_case,
                     preprocessors.words]
    comparator = _misspellings.Misspellings(pathlib.Path(__file__).parent / "english_dictionary.txt")
