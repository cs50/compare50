import sys
from util import ProcessedText, Span
from winnowing import Winnowing

if __name__ == "__main__":
    with open(sys.argv[1], "r") as f:
        print(Winnowing().create_index(ProcessedText([Span(0, f.read())])))
