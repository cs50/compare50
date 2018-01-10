import sys
import os
from preprocessors.nop import Nop
from preprocessors.token_processor import *
from comparators.winnowing import Winnowing

from parsers.c.CLexer import CLexer
from parsers.python.Python3Lexer import Python3Lexer


def preprocess_and_fingerprint():
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


def compare_two():
    def index(filename):
        preprocessor = Nop()
        comparator = Winnowing(16, 24)
        with open(filename, "r") as f:
            text = f.read()
        return comparator.create_index(filename, preprocessor.process(text))
    index1 = index(sys.argv[1])
    index2 = index(sys.argv[2])
    print(index1.compare(index2))


def similarities():
    def index(filename):
        # preprocessor = Nop()
        preprocessor = TokenProcessor(Python3Lexer, NormalizeIdentifiers())
        comparator = Winnowing(16, 32)
        with open(filename, "r") as f:
            text = f.read()
        return comparator.create_index(filename, preprocessor.process(text))
    dirs = [f"Similarities/{d}" for d in os.listdir("Similarities")
            if os.path.isdir(f"Similarities/{d}")]
    helpers = [f"{d}/helpers.py" for d in dirs]
    idx = index(helpers[0])
    for helper in helpers[1:]:
        idx.extend(index(helper))
    for result in idx.compare(idx)[:8]:
        with open(result.id1, "r") as f:
            text1 = f.read()
        with open(result.id2, "r") as f:
            text2 = f.read()
        print(result.report_colored(text1, text2))


if __name__ == "__main__":
    # preprocess_and_fingerprint()
    # compare_two()
    similarities()
