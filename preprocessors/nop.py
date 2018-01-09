from util import TextSpan, ProcessedText


class Nop(object):

    def process(self, text):
        return ProcessedText([TextSpan(0, len(text), text)])
