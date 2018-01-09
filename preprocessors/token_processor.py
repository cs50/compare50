import antlr4
from parsers.c.CLexer import CLexer
from parsers.python.Python3Lexer import Python3Lexer

from util import TextSpan, ProcessedText


class BaseMapper(object):
    def process(self, tokens):
        """Detect language and dispatch to specialized subclass method"""
        if not tokens:
            return tokens
        # remove 'Lexer' from lexer name to get language
        lang = tokens[0].getTokenSource().__class__.__name__[:-5]
        return getattr(self, "process" + lang)(tokens)


class NormalizeIdentifiers(BaseMapper):
    """Replaces all identifiers with `v`"""
    def processPython3(self, tokens):
        for tok in tokens:
            if tok.type == Python3Lexer.NAME:
                tok.text = "v"
        return tokens

    def processC(self, tokens):
        for tok in tokens:
            if tok.type == CLexer.Identifier:
                tok.text = "v"
        return tokens


class NormalizeStringLiterals(BaseMapper):
    """Replaces string literals with empty strings"""
    def processPython3(self, tokens):
        str_types = [Python3Lexer.STRING_LITERAL, Python3Lexer.BYTES_LITERAL]
        for tok in tokens:
            if tok.type in str_types:
                tok.text = '""'
        return tokens

    def processC(self, tokens):
        for tok in tokens:
            if tok.type == CLexer.StringLiteral:
                tok.text = '""'
            if tok.type == CLexer.CharacterConstant:
                tok.text = "''"
        return tokens


class NormalizeNumericLiterals(BaseMapper):
    """Replaces numeric literals with their types"""
    def processPython3(self, tokens):
        int_types = [
            Python3Lexer.DECIMAL_INTEGER,
            Python3Lexer.OCT_INTEGER,
            Python3Lexer.HEX_INTEGER,
            Python3Lexer.BIN_INTEGER
        ]
        for tok in tokens:
            if tok.type in int_types:
                tok.text = "INT"
            elif tok.type == Python3Lexer.FLOAT_NUMBER:
                tok.text = "FLOAT"
            elif tok.type == Python3Lexer.IMAG_NUMBER:
                tok.text = "IMAG"
        return tokens

    def processC(self, tokens):
        float_types = [CLexer.FloatingConstant, CLexer.FractionalConstant]
        for tok in tokens:
            if tok.type == CLexer.IntegerConstant:
                tok.text = "INT"
            elif tok.type in float_types:
                tok.text = "FLOAT"
        return tokens


class ExtractIdentifiers(BaseMapper):
    """Keeps only the first instance of each identifier used"""
    def extractIDs(self, tokens, id_tok_type):
        id_toks = []
        for tok in tokens:
            if tok.type == id_tok_type:
                if not any(id.text == tok.text for id in id_toks):
                    id_toks.append(tok)
        return id_toks

    def processPython3(self, tokens):
        return self.extractIDs(tokens, Python3Lexer.NAME)

    def processC(self, tokens):
        return self.extractIDs(tokens, CLexer.Identifier)


class TokenPrinter(object):
    """Prints the tokens but does not modify them. Useful for debugging."""
    def process(self, tokens):
        for tok in tokens:
            print(tok.text, end="")
        print()
        return tokens


class TextEmitter(object):
    """Emits tokens to spans using their text contents"""
    def emit(self, tokens):
        return ProcessedText([TextSpan(tok.start, tok.stop, tok.text)
                              for tok in tokens])


class TypeEmitter(object):
    """Emits tokens to spans by token type, rather than by contents"""
    def emit(self, tokens):
        return ProcessedText([TextSpan(tok.start, tok.stop, f"{tok.type:X}")
                              for tok in tokens])


class TokenProcessor(object):
    """A preprocessor that composes multiple functions of token streams
    and an emitter"""
    def __init__(self, lexer, *mappers, emitter=TextEmitter()):
        self.lexer = lexer
        self.mappers = mappers
        self.emitter = emitter

    def process(self, text):
        input = antlr4.InputStream(text)
        lexer = self.lexer(input)
        stream = antlr4.CommonTokenStream(lexer)
        stream.fill()
        tokens = stream.tokens
        for mapper in self.mappers:
            tokens = mapper.process(tokens)
        return self.emitter.emit(tokens)
