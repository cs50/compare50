from preprocessors import *
from winnowing import *

# map pass names to (preprocessors, comparator) pairs
DEFAULT_CONFIG = {
    "strip_ws": ([strip_whitespace,
                  by_character],
                 Winnowing(16, 32)),
    "strip_all": ([strip_whitespace,
                   strip_comments,
                   normalize_identifiers,
                   normalize_string_literals],
                  Winnowing(10, 20))
}
