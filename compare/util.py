class Span(object):
    __slots__ = ["_start", "_stop", "_file"]
    def __init__(self, start, stop, file):
        self._start = start
        self._stop = stop
        self._file = file

    @property
    def start(self):
        return self._start

    @property
    def stop(self):
        return self._stop

    @property
    def file(self):
        return self._file

    @staticmethod
    def coalesce(spans):
        """Given a list of spans, return an equivalent list of non-overlapping
        spans"""
        if not spans:
            return None
        file_map = {}
        for span in spans:
            file_map.setdefault(span.file, []).append(span)
        results = []
        for f, spans in file_map.items():
            spans = sorted(spans, key=lambda s: s.start)
            coalesced = [spans[0]]
            for span in spans[1:]:
                if span.start <= coalesced[-1].stop:
                    if span.stop > coalesced[-1].stop:
                        coalesced[-1] = Span(coalesced[-1].start, span.stop, f)
                else:
                    coalesced.append(span)
            results.extend(coalesced)
        return results

    def __repr__(self):
        return f"Span({self.file}:{self.start}:{self.stop})"


class ProcessedText(object):
    """A sequence of (fragment, span) pairs"""
    def __init__(self, spans):
        self._spans = spans

    @property
    def spans(self):
        return self._spans

    def chars(self):
        for fragment, span in self.spans:
            for i, c in enumerate(fragment):
                yield (span.start + i, c)
