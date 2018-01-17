import statistics
from termcolor import colored


class Span(object):
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

    @staticmethod
    def highlight(spans, text, color="red"):
        if not spans:
            return text
        non_match = [text[:spans[0].start]]
        for i in range(1, len(spans)):
            non_match.append(text[spans[i-1].stop:spans[i].start])
        match = [colored(text[s.start:s.stop], color) for s in spans]
        combined = []
        for i in range(len(non_match) + len(match)):
            if i % 2 == 0:
                combined.append(non_match.pop(0))
            else:
                combined.append(match.pop(0))
        return "".join(combined)

    def __repr__(self):
        return f"Span({self.start}:{self.stop})"


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


class Match(object):
    def __init__(self, weight, id1, spans1, id2, spans2):
        keep_order = id1 <= id2
        self._weight = weight
        self._id1 = id1 if keep_order else id2
        self._spans1 = spans1 if keep_order else spans2
        self._id2 = id2 if keep_order else id1
        self._spans2 = spans2 if keep_order else spans1

    def __repr__(self):
        return (f"Match({self.weight}, " +
                f"{self.id1}{self.spans1}, {self.id2}{self.spans2})")

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

    def id_pair(self):
        return (self.id1, self.id2)

    @staticmethod
    def ordered(matches):
        return sorted(matches, key=lambda m: m.weight, reverse=True)

    @staticmethod
    def combine(match_lists, weights=None):
        """Normalizes and optionally weights each list of matches in
        `match_lists`, and combines like matches from the lists to create a
        final ordering of matches"""
        combined_matches = {}
        for i, match_list in enumerate(match_lists):
            scores = [m.weight for m in match_list]
            mean = statistics.mean(scores)
            stdev = statistics.pstdev(scores) if len(match_list) > 1 else 1
            mult = weights[i] if weights else 1
            for match in match_list:
                adjusted_weight = (match.weight - mean) / stdev * mult
                acc = combined_matches.get(match.id_pair())
                if acc:
                    acc = Match(acc.weight + adjusted_weight,
                                match.id1,
                                Span.coalesce(acc.spans1 + match.spans1),
                                match.id2,
                                Span.coalesce(acc.spans2 + match.spans2))
                else:
                    acc = Match(adjusted_weight,
                                match.id1,
                                match.spans1,
                                match.id2,
                                match.spans2)
                combined_matches[match.id_pair()] = acc
        return Match.ordered(combined_matches.values())
