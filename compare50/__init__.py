def _set_version():
    """Set compare50 __version__"""
    global __version__
    from importlib.metadata import version
    try:
        __version__ = version('compare50')
    except:
        __version__ = "version information not available"


# Encapsulated inside a function so their local variables/imports aren't seen by autocompleters
_set_version()

from ._api import *
from ._data import *
from . import comparators, preprocessors, passes
