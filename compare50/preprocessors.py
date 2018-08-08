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
        if tok.type not in (Comment.Multiline, Comment.Single, Comment.Hashbang):
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
    prev_tok = Token(None, None, None, None)
    for tok in tokens:
        if tok.type in String:
            if prev_tok.type not in String:
                yield tok
        elif prev_tok.type in String:
            yield prev_tok
            yield tok
        else:
            yield tok
        prev_tok = tok

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


def comments(tokens):
    """Remove all other tokens except comments."""

    for t in tokens:
        if t.type == Comment.Single or t.type == Comment.Multiline:
            return t

def words(tokens):
    """Split Tokens into Tokens containing just one word."""
    for t in tokens:
        start = t.start
        only_alpha = re.sub("[^a-zA-Z'_-]", " ", t.val)
        for val, (start, end) in [(m.group(0), (m.start(), m.end())) for m in re.finditer(r'\S+', only_alpha)]:
Z           yield Token(t.start + start, t.start + end, t.type, val)
