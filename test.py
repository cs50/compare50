import sys
from util import ProcessedText, Span
from comparators.winnowing import Winnowing

import antlr4

from parsers.c.CLexer import CLexer
from parsers.python.Python3Lexer import Python3Lexer


if __name__ == "__main__":
    input = antlr4.FileStream(sys.argv[1])
    lexer = Python3Lexer(input)
    stream = antlr4.CommonTokenStream(lexer)
    stream.fill()
    tokens = stream.tokens
    # for tok in tokens:
    #     print(str(tok))
    for tok in tokens:
        print((tok.text, tok.start))

    for tok in tokens:
        print(tok.text, end="")

    with open(sys.argv[1], "r") as f:
        print(Winnowing().create_index(ProcessedText([Span(0, f.read())])))
