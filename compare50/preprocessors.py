import re

import attr
from pygments.token import Comment, Name, Number, String, Text, Keyword

from ._data import Token


def strip_whitespace(tokens):
    """Remove all whitespace from tokens."""
    for tok in tokens:
        val = tok.val
        if tok.type in Text:
            val = "".join(tok.val.split())
        if val:
            tok.val = val
            yield tok


def normalize_builtin_types(tokens):
    """Normalize builtin type names"""
    for tok in tokens:
        if tok.type in Keyword.Type:
            tok.val = "t"
        yield tok


def strip_comments(tokens):
    """Remove all comments from tokens."""
    for tok in tokens:
        if tok.type not in (Comment.Multiline, Comment.Single, Comment.Hashbang):
            yield tok


def normalize_case(tokens):
    """Make all tokens lower case."""
    for tok in tokens:
        tok.val = tok.val.lower()
        yield tok


def normalize_identifiers(tokens):
    """Replace all identifiers with ``v``"""
    for tok in tokens:
        if tok.type in Name:
            tok.val = "v"
        yield tok


def normalize_string_literals(tokens):
    """Replace string literals with empty strings."""
    string_token = None
    for tok in tokens:
        if tok.type in String:
            if string_token is None:
                string_token = attr.evolve(tok, val='""')
            elif tok.type == string_token.type:
                string_token.end = tok.end
            else:
                yield string_token
                string_token = attr.evolve(tok, val='""')
        else:
            if string_token is not None:
                yield string_token
                string_token = None
            yield tok


def normalize_numeric_literals(tokens):
    """Replace numeric literals with their types."""
    for tok in tokens:
        if tok.type in Number.Integer:
            tok.val = "INT"
            yield tok
        elif tok.type in Number.Float:
            tok.val = "FLOAT"
            yield tok
        elif tok.type in Number:
            tok.val = "NUM"
            yield tok
        else:
            yield tok


def extract_identifiers(tokens):
    """Remove all tokens that don't represent identifiers."""
    for tok in tokens:
        if tok.type in Name:
            yield tok


def by_character(tokens):
    """Make a token for each character."""
    for tok in tokens:
        for i, c in enumerate(tok.val):
            yield Token(start=tok.start + i,
                        end=tok.start + i + 1,
                        type=Text,
                        val=c)


def token_printer(tokens):
    """Print each token. Useful for debugging."""
    for tok in tokens:
        print(tok)
        yield tok


def text_printer(tokens):
    """Print token values. Useful for debugging."""
    for tok in tokens:
        print(tok.val, end="")
        yield tok


def comments(tokens):
    """Remove all tokens that aren't comments."""
    for t in tokens:
        if t.type == Comment.Single or t.type == Comment.Multiline:
            yield t


def words(tokens):
    """Split tokens into tokens containing just one word."""
    for t in tokens:
        start = t.start
        only_alpha = re.sub("[^a-zA-Z'_-]", " ", t.val)
        for val, (start, end) in ((m.group(0), (m.start(), m.end())) for m in re.finditer(r'\S+', only_alpha)):
            yield Token(t.start + start, t.start + end, t.type, val)


def split_on_whitespace(tokens):
    """Split values of tokens on whitespace into new tokens"""
    for t in tokens:
        start = t.start
        for val, (start, end) in ((m.group(0), (m.start(), m.end())) for m in re.finditer(r'\S+', t.val)):
            yield Token(t.start + start, t.start + end, t.type, val)
