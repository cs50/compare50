from pygments.lexer import RegexLexer
from pygments.token import Text, Name

class WordLexer(RegexLexer):
    """Custom compare50 lexer that creates a token based on each 'word'."""
    name = "WordLexer"
    aliases = ["word"]
    filenames = ["*.txt"]

    tokens = {
        "root": [
            (r"\s+", Text),           # whitespace
            (r"\w+", Name),           # word (alphanumeric)
            (r"\W", Text),            # punctuation or other
        ]
    }
