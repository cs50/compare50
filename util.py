from termcolor import colored


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

    @staticmethod
    def covering(span1, span2):
        return Span(min(span1.start, span2.start), max(span1.stop, span2.stop))

    @staticmethod
    def coalesce(spans):
        if not spans:
            return None
        spans = sorted(spans, key=lambda s: s.start)
        coalesced = [spans[0]]
        for span in spans[1:]:
            if span.start <= coalesced[-1].stop:
                coalesced[-1] = Span(coalesced[-1].start, span.stop)
            else:
                coalesced.append(span)
        return coalesced

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


class Match(object):
    def __init__(self, weight, id1, spans1, id2, spans2):
        self._weight = weight
        self._id1 = id1
        self._spans1 = spans1
        self._id2 = id2
        self._spans2 = spans2

    def __repr__(self):
        return f"Match({self.weight}, {self.id1}{self.spans1}, {self.id2}{self.spans2})"

    @property
    def weight(self):
        return self._weight

    @property
    def id1(self):
        return self._id1

    @property
    def spans1(self):
        return self._spans1

    @property
    def id2(self):
        return self._id2

    @property
    def spans2(self):
        return self._spans2

    def report_colored(self, text1, text2):
        def render_spans(text, spans):
            if not spans:
                return text
            non_match = [text[:spans[0].start]]
            for i in range(1, len(spans)):
                non_match.append(text[spans[i-1].stop:spans[i].start])
            match = [colored(text[s.start:s.stop], 'red') for s in spans]
            combined = []
            for i in range(len(non_match) + len(match)):
                if i % 2 == 0:
                    combined.append(non_match.pop(0))
                else:
                    combined.append(match.pop(0))
            return "".join(combined)
        header = f"{self.id1}, {self.id2} (weight: {self.weight})"
        rendered1 = render_spans(text1, self.spans1)
        rendered2 = render_spans(text2, self.spans2)
        return "".join([header, "\n\n",
                        self.id1, "\n\n", rendered1, "\n\n",
                        self.id2, "\n\n", rendered2, "\n"])
