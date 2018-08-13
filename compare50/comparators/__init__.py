import pathlib
from ..data import Pass
from .. import preprocessors
from . import winnowing
from . import misspellings


class winnowing_ws(Pass):
    """Removes all whitespace and runs Winnowing with k=40, t=60."""
    preprocessors = [preprocessors.strip_whitespace,
                     preprocessors.split_on_whitespace]
    comparator = winnowing.Winnowing(k=40, t=60)


class winnowing_all(Pass):
    """Removes all whitespace, normalizes all comments/ids/strings, and runs Winnowing with k=25, t=35."""

    preprocessors = [preprocessors.strip_whitespace,
                     preprocessors.strip_comments,
                     preprocessors.normalize_identifiers,
                     preprocessors.normalize_string_literals,
                     preprocessors.normalize_numeric_literals]
    comparator = winnowing.Winnowing(k=25, t=35)


class misspellings_en(Pass):
    """Compares comments for identical English word misspellings."""

    preprocessors = [preprocessors.comments,
                     preprocessors.normalize_case,
                     preprocessors.words]
    comparator = misspellings.Misspellings(pathlib.Path(__file__).parent / "english_dictionary.txt")
