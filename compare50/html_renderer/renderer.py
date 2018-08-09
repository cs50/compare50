import pygments
from pygments.formatters import HtmlFormatter, TerminalFormatter
import collections
import attr
import glob
import os
import shutil
import pathlib
import concurrent.futures as futures

import jinja2

from .. import data, api

@attr.s(slots=True, frozen=True, hash=True)
class Fragment:
    content = attr.ib(convert=lambda c: tuple(c.splitlines(True)))
    spans = attr.ib(default=attr.Factory(tuple), convert=tuple)


def render(submission_groups_list, dest="html"):
    submission_groups = submission_groups_list[-1]

    with api.Executor() as executor:
        update_percentage = api.progress_bar().remaining_percentage / len(submission_groups)
        for id, html in executor.map(_RenderFile(dest), enumerate(submission_groups, 1)):
            with open(dest / f"match_{id}.html", "w") as f:
                f.write(html)
            api.progress_bar().update(update_percentage)


def fragmentize(file, spans):
    slicer = _FragmentSlicer()
    for span in spans:
        slicer.add_span(span)
    return slicer.slice(file)


class _RenderFile:
    def __init__(self, dest):
        self._prepare_dest(dest)
        self.dest = dest
        src = pathlib.Path(__file__).absolute().parent
        js, css, bootstrap, fonts = (self._read_file(src / "static" / name)
                                     for name in ("compare50.js", "compare50.css", "bootstrap.min.css", "fonts.css"))
        self.js = (js,)
        self.css = (fonts, bootstrap, css)

    def __call__(self, args):
        match_id, (sub_a, sub_b, groups, ignored_spans) = args
        frag_id_counter = 0
        span_ids = data.IdStore()
        group_ids = data.IdStore()

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

            sub_chars_in_group = 0
            sub_unignored_chars = 0

            for file in submission.files:
                frag_list = []
                file_chars_in_group = 0
                file_unignored_chars = 0
                for fragment in fragmentize(file, file_to_spans[file]):
                    frag_bytes = sum(len(line) for line in fragment.content)
                    frag_id = f"frag{frag_id_counter}"
                    frag_id_counter += 1
                    is_ignored = any(span in ignored_spans for span in fragment.spans)

                    if not is_ignored:
                        file_unignored_chars += frag_bytes

                    frag_list.append((frag_id, fragment.content, is_ignored))

                    # If span is part of a group, add
                    if any(span not in ignored_spans for span in fragment.spans):
                        if not is_ignored:
                             file_chars_in_group += frag_bytes

                    fragment_to_spans[frag_id] = [span_ids[span] for span in fragment.spans if span not in ignored_spans]

                sub_chars_in_group += file_chars_in_group
                sub_unignored_chars += file_unignored_chars
                file_list.append((str(file.name), frag_list, self._percentage(file_chars_in_group, file_unignored_chars)))

            submissions.append((str(submission.path), file_list, self._percentage(sub_chars_in_group, sub_unignored_chars)))

        content = self._read_file(pathlib.Path(__file__).absolute().parent / "templates/match.html")

        template = jinja2.Template(content, autoescape=jinja2.select_autoescape(enabled_extensions=("html",)))

        # Render
        rendered_html = template.render(fragment_to_spans=fragment_to_spans,
                                        span_to_group=span_to_group,
                                        sub_a=submissions[0],
                                        sub_b=submissions[1],
                                        js=self.js,
                                        css=self.css)

        return match_id, rendered_html

    @staticmethod
    def _read_file(fname):
        with open(fname) as f:
            return f.read()


    @staticmethod
    def _percentage(numerator, denominator, on_error=0):
        try:
            return round(numerator / denominator * 100)
        except ZeroDivisionError:
            return on_error


    @staticmethod
    def _prepare_dest(dest):
        if dest.is_dir():
            for file in glob.glob(str(dest / "match_*.html")):
                try:
                    os.remove(file)
                except IsADirectoryError:
                    # This shouldn't really ever happen, but just in case...
                    shutil.rmtree(file)

            try:
                os.remove(dest / "index.html")
            except IsADirectoryError:
                shutil.rmtree(dest / "index.html")
            except FileNotFoundError:
                pass
        elif dest.is_file():
            os.remove(dest)

        dest.mkdir(exist_ok=True)


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
            fragments.append(Fragment(content[start_mark:mark], sorted(fragment_spans, key=lambda span: span.end - span.start, reverse=True)))
            start_mark = mark

        return fragments

    def add_span(self, span):
        self._slicing_marks.add(span.start)
        self._slicing_marks.add(span.end)
        self._start_to_spans[span.start].add(span)
        self._end_to_spans[span.end].add(span)
