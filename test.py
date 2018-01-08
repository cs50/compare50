import sys
from preprocessors.nop import Nop
from comparators.winnowing import Winnowing

import antlr4

from parsers.c.CLexer import CLexer
from parsers.python.Python3Lexer import Python3Lexer


if __name__ == "__main__":
    with open(sys.argv[1], "r") as f:
        text = f.read()
    input = antlr4.InputStream(text)
    lexer = Python3Lexer(input)
    stream = antlr4.CommonTokenStream(lexer)
    stream.fill()
    tokens = stream.tokens
    for tok in tokens:
        print((tok.text, tok.start))

    for tok in tokens:
        print(tok.text, end="")
    print()

    preprocessor = Nop()
    comparator = Winnowing()
    print(comparator.create_index(preprocessor.process(text)))
