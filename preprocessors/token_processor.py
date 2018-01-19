import pygments
import pygments.lexers
from pygments.token import Token, String, Name, Number

from util import Span, ProcessedText


def strip_whitespace(tokens):
    for start, stop, tok, val in tokens:
        # TODO: strip whitespace from text tokens
        if tok not in Token.Text or not val.isspace():
            yield (start, stop, tok, val)


def strip_comments(tokens):
    for start, stop, tok, val, in tokens:
        if tok not in Token.Comment:
            yield (start, stop, tok, val)


def normalize_case(tokens):
    for start, stop, tok, val, in tokens:
        yield (start, stop, tok, val.lower())


def normalize_identifiers(tokens):
    """Replaces all identifiers with `v`"""
    for start, stop, tok, val in tokens:
        if tok in Name:
            yield (start, stop, tok, "v")
        else:
            yield (start, stop, tok, val)


def normalize_string_literals(tokens):
    """Replaces string literals with empty strings"""
    # True if last token was changed, used to coalesce adjacent strings
    normed = False
    for start, stop, tok, val in tokens:
        if tok in String.Char:
            if not normed:
                yield (start, stop, tok, "''")
            normed = True
        elif tok in String:
            if not normed:
                yield (start, stop, tok, '""')
            normed = True
        else:
            yield (start, stop, tok, val)
            normed = False


def normalize_numeric_literals(tokens):
    """Replaces numeric literals with their types"""
    for start, stop, tok, val in tokens:
        if tok in Number.Integer:
            yield (start, stop, tok, "INT")
        elif tok in Number.Float:
            yield (start, stop, tok, "FLOAT")
        elif tok in Number:
            yield (start, stop, tok, "NUM")
        else:
            yield (start, stop, tok, val)


def extract_identifiers(tokens):
    """Keeps only the first instance of each identifier used"""
    names = []
    for start, stop, tok, val in tokens:
        if tok in Name and val not in names:
            names.append(val)
            yield (start, stop, tok, val)


def buffer(tokens):
    """Collects all tokens in a list before passing them on. Useful for
    serializing side effects of previous and subsequent filters."""
    return list(tokens)


def token_printer(tokens):
    """Prints all token data. Useful for debugging."""
    for t in tokens:
        print(t)
        yield t


def text_printer(tokens):
    """Prints token values. Useful for debugging."""
    for start, stop, tok, val in tokens:
        print(val, end="")
        yield (start, stop, tok, val)


class TokenProcessor(object):
    """A preprocessor that composes multiple functions of token streams"""
    def __init__(self, *mappers):
        self.mappers = mappers

    def process(self, file):
        with open(file, "r") as f:
            text = f.read()

        # try getting lexer by filename then contents, fallback to text lexer
        try:
            lexer = pygments.lexers.get_lexer_for_filename(file)
        except pygments.util.ClassNotFound:
            try:
                lexer = pygments.lexers.guess_lexer(text)
            except pygments.util.ClassNotFound:
                lexer = pygments.lexers.special.TextLexer()

        tokens = list(lexer.get_tokens_unprocessed(text))

        # add end index to token stream
        tokens.append((None, len(text)))
        tokens = [(tokens[i][0], tokens[i+1][0], tokens[i][1], tokens[i][2])
                  for i in range(len(tokens) - 1)]

        # run transformations on tokens
        for mapper in self.mappers:
            tokens = mapper(tokens)

        # produce (fragment, span) output
        spans = [(val, Span(start, stop, file))
                 for start, stop, _, val in tokens]
        return ProcessedText(spans)
