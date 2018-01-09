from util import Span, ProcessedText


class Nop(object):

    def process(self, text):
        return ProcessedText([Span(0, len(text), text)])
