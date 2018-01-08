from util import Span, ProcessedText

class Nop:

    def process(self, text: str) -> ProcessedText:
        return ProcessedText([Span(0, text)])
