import importlib
import atexit
from contextlib import ExitStack

from . import comparators, preprocessors
from ._data import Pass

__all__ = ["structure", "text", "exact", "nocomments", "misspellings"]


class structure(Pass):
    """Compares code structure by removing whitespace and comments; normalizing variable names, string literals, and numeric literals; and then running the winnowing algorithm."""
    default = True
    preprocessors = [preprocessors.strip_whitespace,
                     preprocessors.strip_comments,
                     preprocessors.normalize_identifiers,
                     preprocessors.normalize_builtin_types,
                     preprocessors.normalize_string_literals,
                     preprocessors.normalize_numeric_literals]
    comparator = comparators.Winnowing(k=25, t=35)


class text(Pass):
    """Removes whitespace, then uses the winnowing algorithm to compare submissions."""
    default = True
    preprocessors = [preprocessors.split_on_whitespace,
                     preprocessors.strip_whitespace]
    comparator = comparators.Winnowing(k=25, t=35)


class exact(Pass):
    """Removes nothing, not even whitespace, then uses the winnowing algorithm to compare submissions."""
    default = True
    preprocessors = []
    comparator = comparators.Winnowing(k=25, t=35)


class nocomments(Pass):
    """Removes comments, but keeps whitespace, then uses the winnowing algorithm to compare submissions."""
    preprocessors = [preprocessors.strip_comments, preprocessors.split_on_whitespace]
    comparator = comparators.Winnowing(k=25, t=35)


class misspellings(Pass):
    """Compares comments for identically misspelled English words."""
    preprocessors = [preprocessors.comments,
                     preprocessors.normalize_case,
                     preprocessors.words]

    file_manager = ExitStack()
    atexit.register(file_manager.close)
    ref = importlib.resources.files('compare50.comparators') / 'english_dictionary.txt'
    path = file_manager.enter_context(
        importlib.resources.as_file(ref))

    comparator = comparators.Misspellings(path)
