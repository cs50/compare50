import sys
import os
import pprint
from preprocessors.nop import Nop
from preprocessors.token_processor import *
from comparators.winnowing import Winnowing

from compare import compare


def preprocess_and_fingerprint():
    _, ext = os.path.splitext(sys.argv[1])
    if ext == ".py":
        lang = "Python3"
    elif ext == ".c":
        lang = "C"
    preprocessor = TokenProcessor(
        lang,
        # StripWhitespace(),
        # StripComments(),
        # NormalizeIdentifiers(),
        # NormalizeStringLiterals(),
        # NormalizeNumericLiterals(),
        ExtractIdentifiers(),
        TokenPrinter(),
        Buffer(),
        TextPrinter()
    )
    comparator = Winnowing(12, 24)
    result = comparator.create_index(sys.argv[1], preprocessor)
    print(result)
    print(len(repr(result)))


def compare_two():
    def index(filename):
        preprocessor = Nop()
        comparator = Winnowing(16, 24)
        return comparator.create_index(filename, preprocessor)
    index1 = index(sys.argv[1])
    index2 = index(sys.argv[2])
    print(index1.compare(index2))


def similarities():
    directory = sys.argv[1]
    submission_dirs = [f"{directory}/{d}"
                       for d in os.listdir(f"{directory}")
                       if os.path.isdir(f"{directory}/{d}")]
    submissions = [(f"{d}/helpers.py",) for d in submission_dirs]
    distro = ("similarities/helpers.py",)
    results = compare(distro, submissions)
    pp = pprint.PrettyPrinter(width=1, indent=1, compact=True)
    pp.pprint(results)


if __name__ == "__main__":
    # preprocess_and_fingerprint()
    # compare_two()
    similarities()
