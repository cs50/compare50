def _set_version():
    """Set compare50 __version__"""
    global __version__
    import sys
    from importlib.metadata import PackageNotFoundError, version

    # Require Python 3.8+
    if sys.version_info < (3, 8):
        sys.exit("You have an old version of python. Install version 3.8 or higher.")

    # Get version
    try:
        __version__ = version("compare50")
    except PackageNotFoundError:
        __version__ = "UNKNOWN"


# Encapsulated inside a function so their local variables/imports aren't seen by autocompleters
_set_version()

from ._api import *
from ._data import *
from . import comparators, preprocessors, passes
