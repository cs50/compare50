class Span(object):
    """A contiguous string `text` from positions `start` to `stop` in a file"""
    def __init__(self, start, stop, text):
        self._start = start
        self._stop = stop
        self._text = text

    @property
    def start(self):
        return self._start

    @property
    def stop(self):
        return self._stop

    @property
    def text(self):
        return self._text


class ProcessedText(object):
    """A sequence of spans"""
    def __init__(self, spans):
        self.spans = spans

    def __str__(self):
        return "".join(span.text for span in self.spans)

    def chars(self):
        for span in self.spans:
            for i, c in enumerate(span.text):
                yield (span.start + i, c)
