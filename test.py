import sys
import os
from preprocessors.nop import Nop
from preprocessors.token_processor import *
from comparators.winnowing import Winnowing

from parsers.c.CLexer import CLexer
from parsers.python.Python3Lexer import Python3Lexer


if __name__ == "__main__":
    _, ext = os.path.splitext(sys.argv[1])
    if ext == ".py":
        lexer = Python3Lexer
    elif ext == ".c":
        lexer = CLexer
    with open(sys.argv[1], "r") as f:
        text = f.read()
    preprocessor = TokenProcessor(
        lexer,
        NormalizeIdentifiers(),
        NormalizeStringLiterals(),
        NormalizeNumericLiterals(),
        # ExtractIdentifiers(),
        TokenPrinter()
    )
    comparator = Winnowing(12, 24)
    result = comparator.create_index(sys.argv[1], preprocessor.process(text))
    print(result)
    print(len(repr(result)))
