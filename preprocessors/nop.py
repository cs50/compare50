from util import Span, ProcessedText


class Nop(object):

    def process(self, file):
        with open(file, "r") as f:
            text = f.read()
        return ProcessedText([(text, Span(0, len(text), file))])
