import attr
from pygments.token import Comment, Name, Number, String, Text

from .data import Token

def strip_whitespace(tokens):
    for tok in tokens:
        val = tok.val
        if tok.type in Text:
            val = "".join(tok.val.split())
        if val:
            tok.val = val
            yield tok
            #yield attr.evolve(tok, val=val)


def strip_comments(tokens):
    for tok in tokens:
        if tok.type not in Comment:
            yield tok


def normalize_case(tokens):
    for tok in tokens:
        tok.val = tok.val.lower()
        yield tok
        #yield attr.evolve(tok, tok.val.lower())


def normalize_identifiers(tokens):
    """Replaces all identifiers with `v`"""
    for tok in tokens:
        if tok.type in Name:
            tok.val = "v"
            yield tok
            #yield attr.evolve(tok, val="v")
        else:
            yield tok


def normalize_string_literals(tokens):
    """Replaces string literals with empty strings"""
    # True if last token was changed, used to coalesce adjacent strings
    normed = False
    for tok in tokens:
        if tok.type in String.Char:
            if not normed:
                tok.val = "''"
                yield tok
                #yield attr.evolve(tok, val="''")
            normed = True
        elif tok.type in String:
            if not normed:
                tok.val = "''"
                yield tok
                #yield attr.evolve(tok, val='""')
            normed = True
        else:
            yield tok
            normed = False


def normalize_numeric_literals(tokens):
    """Replaces numeric literals with their types"""
    for tok in tokens:
        if tok.type in Number.Integer:
            tok.val = "INT"
            yield tok
            #yield attr.evolve(tok, val="INT")
        elif tok.type in Number.Float:
            tok.val = "FLOAT"
            yield tok
            #yield attr.evolve(tok, val="FLOAT")
        elif tok.type in Number:
            tok.val = "NUM"
            yield tok
            #yield attr.evolve(tok, val="NUM")
        else:
            yield tok


def extract_identifiers(tokens):
    """Keeps only the first instance of each identifier used"""
    for tok in tokens:
        if tok.type in Name:
            yield tok

def by_character(tokens):
    for tok in tokens:
        for i, c in enumerate(tok.val):
            yield Token(start=tok.start + i,
                        end=tok.start + i + 1,
                        type=Text,
                        val=c)


def buffer(tokens):
    """Collects all tokens in a list before passing them on. Useful for
    serializing side effects of previous and subsequent filters."""
    return list(tokens)


def token_printer(tokens):
    """Prints all token data. Useful for debugging."""
    for tok in tokens:
        print(tok)
        yield tok


def text_printer(tokens):
    """Prints token values. Useful for debugging."""
    for tok in tokens:
        print(tok.val, end="")
        yield tok
