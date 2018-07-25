from .data import _IdStore
import pygments
from pygments.formatters import HtmlFormatter, TerminalFormatter
import collections
import attr

class Fragments:
    def __init__(self, file):
        with open(file.path) as f:
            content = f.read()
        self._index = [(0, Fragment(content))]

    @property
    def content(self):
        return [fragment for _, fragment in self._index]

    def add_span(self, span):
        index = []

        is_assigning = False
        for start, fragment in self._index:
            end = start + len(fragment.content)

            # If span cuts into fragment, split fragment
            if start <= span.start <= end or start <= span.stop <= end:

                # Decide on indices on which to split
                # Split fragments
                # Add span to fragment
                if start <= span.start <= end and start <= span.stop <= end:
                    is_assigning = True
                    frags = fragment.split(span.start - start, span.stop - start)
                    frags[1].spans.add(span)
                elif start <= span.start <= end:
                    is_assigning = True
                    frags = fragment.split(span.start - start)
                    frags[1].spans.add(span)
                elif start <= span.stop <= end:
                    is_assigning = False
                    frags = fragment.split(span.stop - start)
                    frags[0].spans.add(span)

                # Add new frags to index
                new_start = start
                for frag in frags:
                    index.append((new_start, frag))
                    new_start += len(frag.content)
            else:
                index.append((start, fragment))
                if is_assigning:
                    fragment.spans.add(span)

        self._index = index


@attr.s(slots=True)
class Fragment:
    content = attr.ib()
    spans = attr.ib(default=attr.Factory(set))

    def split(self, index, *indices):
        indices = [index] + list(indices) + [len(self.content)]
        fragments = []
        start_index = 0
        for index in indices:
            content = self.content[start_index:index]
            fragments.append(Fragment(content, set(self.spans)))
            start_index = index
        return fragments


def render(submission_groups):
    for sub_a, sub_b, groups in submission_groups:
        span_to_group = {}
        file_to_spans = collections.defaultdict(list)

        for group in groups:
            for span in group.spans:
                file_to_spans[span.file].append(span)
                span_to_group[span] = group

        for file in file_to_spans:
            fragments = fragmentize(file, file_to_spans[file])
            render_file(file, fragments, span_to_group)


def render_file(file, fragments, span_to_group):
    formatter = TerminalFormatter(linenos=True, bg="dark")
    print("*" * 80)
    print(file.name)
    print("*" * 80)
    for fragment in fragments:
        groups = list({span_to_group[span] for span in fragment.spans})
        print(pygments.highlight(fragment.content, file.lexer(), formatter))
        print("Spans:", fragment.spans)
        print("Number of groups:", len(groups))
        print("Matches with:", [group.spans for group in groups])
        print("=" * 80)


def fragmentize(file, spans):
    fragments = Fragments(file)
    for span in spans:
        fragments.add_span(span)
    return fragments.content





#
#     return
#
#     dest = pathlib.Path(dest)
#
#     if not dest.exists():
#         os.mkdir(dest)
#
#     subs_to_groups = collections.defaultdict(list)
#
#     for group in groups:
#         subs_to_groups[(group.sub_a, group.sub_b)].append(group)
#
#     subs_groups = [(sm.sub_a, sm.sub_b, subs_to_groups[(sm.sub_a, sm.sub_b)]) for sm in submission_matches]
#
#     formatter = HtmlFormatter(linenos=True)
#
#     with open(dest / "style.css", "w") as f:
#         f.write(formatter.get_style_defs('.highlight'))
#
#     for i, (sub_a, sub_b, groups) in enumerate(subs_groups):
#         with open(dest / "match_{}.html".format(i), "w") as f:
#             f.write('<link rel="stylesheet" type="text/css" href="{}">'.format("style.css"))
#             f.write("{} {}<br/>".format(sub_a.path, sub_b.path))
#
#             for group in groups:
#                 f.write(" ".join(str(span) for span in group.spans))
#                 f.write("<br/>")
#
#             for html in mark_matches(sub_a, sub_b, groups, formatter):
#                 f.write(html)
#
#             # for sub in (sub_a, sub_b):
#             #     for file in sub.files():
#             #         with open(file.path) as in_file:
#             #             f.write(mark_matches(in_file.read(), formatter, file.lexer()))
#
# def mark_matches(sub_a, sub_b, groups, formatter):
#     htmls = []
#     for file in sub_a.files():
#         file_spans = [span for group in groups for span in group.spans if span.file.id == file.id]
#         with open(file.path) as f:
#             highlighted_html = pygments.highlight(f.read(), file.lexer(), formatter)
#
#         soup = BeautifulSoup(highlighted_html, 'html.parser')
#         for s in soup.find_all("span"):
#             print(dir(s))
#             print(s.contents)
#
#         htmls.append(str(soup))
#
#     return htmls
