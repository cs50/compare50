from pygments.lexers.c_cpp import CLexer
from pygments.lexers.python import Python3Lexer
from pygments.token import Token, String, Name, Number

from util import TextSpan, ProcessedText


class NormalizeIdentifiers(object):
    """Replaces all identifiers with `v`"""
    def process(self, language, tokens):
        for start, stop, tok, val in tokens:
            if tok in Name:
                yield (start, stop, tok, "v")
            else:
                yield (start, stop, tok, val)


class NormalizeStringLiterals(object):
    """Replaces string literals with empty strings"""
    def process(self, language, tokens):
        for start, stop, tok, val in tokens:
            if tok in String.Char:
                yield (start, stop, tok, "''")
            elif tok in String:
                yield (start, stop, tok, '""')
            else:
                yield (start, stop, tok, val)


class NormalizeNumericLiterals(object):
    """Replaces numeric literals with their types"""
    def process(self, language, tokens):
        for start, stop, tok, val in tokens:
            if tok in Number.Integer:
                yield (start, stop, tok, "INT")
            elif tok in Number.Float:
                yield (start, stop, tok, "FLOAT")
            elif tok in Number:
                yield (start, stop, tok, "NUM")


class ExtractIdentifiers(object):
    """Keeps only the first instance of each identifier used"""
    def process(self, language, tokens):
        names = []
        for start, stop, tok, val in tokens:
            if tok in Name and val not in names:
                names.append(val)
                yield (start, stop, tok, val)


class TokenPrinter(object):
    """Prints the tokens but does not modify them. Useful for debugging."""
    def process(self, language, tokens):
        for start, stop, tok, val in tokens:
            print(val, end="")
            yield (start, stop, tok, val)


class TokenProcessor(object):
    """A preprocessor that composes multiple functions of token streams"""
    def __init__(self, language, *mappers):
        self.language = language
        self.lexer = {"Python3": Python3Lexer, "C": CLexer}[language]
        self.mappers = mappers

    def process(self, text):
        lexer = self.lexer()
        tokens = list(lexer.get_tokens_unprocessed(text))
        tokens.append((None, len(text)))
        tokens = [(tokens[i][0], tokens[i+1][0], tokens[i][1], tokens[i][2])
                  for i in range(len(tokens) - 1)]
        for t in tokens: print(t)
        for mapper in self.mappers:
            tokens = mapper.process(self.language, tokens)
        spans = [TextSpan(start, stop, val) for start, stop, _, val in tokens]
        return ProcessedText(spans)
