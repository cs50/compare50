class Span(object):
    def __init__(self, start, stop):
        self._start = start
        self._stop = stop

    @property
    def start(self):
        return self._start

    @property
    def stop(self):
        return self._stop

    def covering(span1, span2):
        return Span(min(span1.start, span2.start), max(span1.stop, span2.stop))

    def __repr__(self):
        return f"Span({self.start}:{self.stop})"


class TextSpan(object):
    """A contiguous string `text` from positions `start` to `stop` in a file"""
    def __init__(self, start, stop, text):
        self._start = start
        self._stop = stop
        self._text = text

    @property
    def text(self):
        return self._text

    @property
    def start(self):
        return self._start

    @property
    def stop(self):
        return self._stop

class ProcessedText(object):
    """A sequence of text spans"""
    def __init__(self, spans):
        self._spans = spans

    @property
    def spans(self):
        return self._spans

    def chars(self):
        for span in self.spans:
            for i, c in enumerate(span.text):
                yield (span.start + i, c)
