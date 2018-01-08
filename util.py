class Span(object):
    """A contiguous chunk of text `s` from position `pos` in a file"""
    def __init__(self, pos, s):
        self.pos = pos
        self.s = s


class ProcessedText(object):
    """A sequence of spans"""
    def __init__(self, spans):
        self.spans = spans

    def __str__(self):
        "".join([span.s for span in self.spans])

    def chars(self):
        for span in self.spans:
            for i, c in enumerate(span.s):
                yield (span.pos + i, c)
