from ..data import IdStore
import pygments
from pygments.formatters import HtmlFormatter, TerminalFormatter
import collections
import attr
import shutil
import pathlib

import jinja2


@attr.s(slots=True, frozen=True, hash=True)
class Fragment:
    content = attr.ib(convert=lambda c: tuple(c.splitlines(True)))
    spans = attr.ib(default=attr.Factory(tuple), convert=tuple)


def render(submission_groups, dest="html"):
    src = pathlib.Path(__file__).absolute().parent
    dest = pathlib.Path(dest)
    if dest.exists():
        shutil.rmtree(dest)
    dest.mkdir()

    def read_file(fname):
        with open(fname) as f:
            return f.read()

    js, css, bootstrap, fonts = (read_file(src / "static" / name)
                         for name in ("compare50.js", "compare50.css", "bootstrap.min.css", "fonts.css"))

    for match_id, (sub_a, sub_b, groups, ignored_spans) in enumerate(submission_groups):
        frag_id_counter = 0
        span_ids = IdStore()
        group_ids = IdStore()

        span_to_group = {}
        file_to_spans = collections.defaultdict(list)
        fragment_to_spans = {}

        for group in groups:
            group_id = group_ids[group]
            for span in group.spans:
                span_to_group[span_ids[span]] = group_id
                file_to_spans[span.file].append(span)

        for span in ignored_spans:
            file_to_spans[span.file].append(span)

        ignored_spans = set(ignored_spans)

        submissions = []
        for submission in (sub_a, sub_b):
            file_list = []
            for file in submission.files:
                frag_list = []
                for fragment in fragmentize(file, file_to_spans[file]):
                    frag_id = f"frag{frag_id_counter}"
                    frag_id_counter += 1
                    is_ignored = any(span in ignored_spans for span in fragment.spans)
                    frag_list.append((frag_id, fragment.content, is_ignored))

                    # If span is part of a group, add
                    if any(span not in ignored_spans for span in fragment.spans):
                        fragment_to_spans[frag_id] = [span_ids[span] for span in fragment.spans if span not in ignored_spans]
                file_list.append((str(file.name), frag_list))
            submissions.append((str(submission.path), file_list))

        # Get template
        with open(pathlib.Path(__file__).absolute().parent / "templates/match.html") as f:
            content = f.read()

        template = jinja2.Template(content, autoescape=jinja2.select_autoescape(enabled_extensions=("html",)))

        # Render
        rendered_html = template.render(fragment_to_spans=fragment_to_spans,
                                        span_to_group=span_to_group,
                                        sub_a=submissions[0],
                                        sub_b=submissions[1],
                                        js=(js,),
                                        css=(fonts, bootstrap, css))

        with open(dest / f"match_{match_id}.html", "w") as f:
            f.write(rendered_html)

def fragmentize(file, spans):
    slicer = _FragmentSlicer()
    for span in spans:
        slicer.add_span(span)
    return slicer.slice(file)


class _FragmentSlicer:
    def __init__(self):
        self._slicing_marks = set()
        self._start_to_spans = collections.defaultdict(set)
        self._end_to_spans = collections.defaultdict(set)

    def slice(self, file):
        # Slicing at 0 has no effect, so remove
        self._slicing_marks.discard(0)

        # Get file content
        with open(file.path) as f:
            content = f.read()

        # If there are no slicing marks, return entire file in one fragment
        if not self._slicing_marks:
            return [Fragment(content)]

        # Perform slicing in order
        slicing_marks = sorted(self._slicing_marks)

        # Create list of spans at every fragment
        spans = [self._start_to_spans[0] - self._end_to_spans[0]]
        for mark in slicing_marks:
            cur = set(spans[-1])
            cur |= self._start_to_spans[mark]
            cur -= self._end_to_spans[mark]
            spans.append(cur)

        # Make sure that last slice ends at the last index in file
        if slicing_marks and slicing_marks[-1] < len(content):
            slicing_marks.append(len(content))

        # Split fragments from file
        fragments = []
        start_mark = 0
        for fragment_spans, mark in zip(spans, slicing_marks):
            fragments.append(Fragment(content[start_mark:mark], sorted(fragment_spans, key=lambda span: span.end - span.start)))
            start_mark = mark

        return fragments

    def add_span(self, span):
        self._slicing_marks.add(span.start)
        self._slicing_marks.add(span.end)
        self._start_to_spans[span.start].add(span)
        self._end_to_spans[span.end].add(span)



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
