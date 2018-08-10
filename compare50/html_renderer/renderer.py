import collections
import glob
import os
import pathlib
import shutil

import attr
import jinja2
import pygments
from pygments.formatters import HtmlFormatter, TerminalFormatter

from .. import api
from ..data import IdStore

@attr.s(slots=True)
class Fragment:
    content = attr.ib(convert=lambda c: tuple(c.splitlines(True)))
    spans = attr.ib(default=attr.Factory(tuple), convert=tuple)


@attr.s(slots=True)
class Data:
    span_to_group = attr.ib()
    fragment_to_spans = attr.ib()


@attr.s(slots=True)
class HTML_Fragment:
    id = attr.ib()
    content = attr.ib()
    is_ignored = attr.ib()
    is_grouped = attr.ib()
    spans = attr.ib()


@attr.s(slots=True)
class HTML_File:
    name = attr.ib()
    fragments = attr.ib()
    num_chars_matched = attr.ib()
    num_chars = attr.ib()

    @property
    def percentage(self):
        try:
            return round(self.num_chars_matched / self.num_chars * 100)
        except ZeroDivisionError:
            return 0


@attr.s(slots=True)
class HTML_Submission:
    name = attr.ib()
    files = attr.ib()
    num_chars_matched = attr.ib()
    num_chars = attr.ib()

    @property
    def percentage(self):
        try:
            return round(self.num_chars_matched / self.num_chars * 100)
        except ZeroDivisionError:
            return 0


def render(submission_groups_list, dest):
    submission_groups = submission_groups_list[-1]
    dest = pathlib.Path(dest)

    sub_match_to_submissions_groups = collections.defaultdict(list)
    for submission_groups in submission_groups_list:
        for sg in submission_groups:
            score, groups, ignored_spans = sg
            sub_match_to_submissions_groups[(score.sub_a, score.sub_b)].append(sg)

    # Sort by score
    submission_groups = sorted(sub_match_to_submissions_groups.values(), key=lambda sg: sg[0], reverse=True)

    with api.Executor() as executor:
        update_percentage = api.progress_bar().remaining_percentage / (len(submission_groups) + 1)
        _render_file = _RenderTask(dest)
        for id, html in executor.map(_RenderTask(dest), enumerate(submission_groups, 1)):
            with open(dest / f"match_{id}.html", "w") as f:
                f.write(html)
            api.progress_bar().update(update_percentage)


    src = pathlib.Path(__file__).absolute().parent
    with open(src / "templates" / "index.html") as f:
        index_template = jinja2.Template(f.read(), autoescape=jinja2.select_autoescape(enabled_extensions=("html",)))

    # Render
    rendered_html = index_template.render(css=_render_file.css[:-1], scores=[group[0][0] for group in submission_groups], dest=dest.resolve())

    with open(dest / "index.html", "w") as f:
        f.write(rendered_html)
    api.progress_bar().update(update_percentage)
    return dest / "index.html"



def fragmentize(file, spans):
    slicer = _FragmentSlicer()
    for span in spans:
        slicer.add_span(span)
    return slicer.slice(file)


class _RenderTask:
    def __init__(self, dest):
        self._prepare_dest(dest)
        self.dest = dest
        src = pathlib.Path(__file__).absolute().parent
        js, css, bootstrap, fonts = (self._read_file(src / "static" / name)
                                     for name in ("compare50.js", "compare50.css", "bootstrap.min.css", "fonts.css"))
        self.js = (js,)
        self.css = (fonts, bootstrap, css)

    def __call__(self, args):
        match_id, (submissions_groups) = args
        for submission_group in submissions_groups:
            score, groups, ignored_spans = submission_group
            renderer = _Renderer()

            file_to_spans = collections.defaultdict(list)

            for group in groups:
                for span in group.spans:
                    file_to_spans[span.file].append(span)

            for span in ignored_spans:
                file_to_spans[span.file].append(span)

            ignored_spans = set(ignored_spans)
            sub_a = renderer.html_submission(score.sub_a, file_to_spans, ignored_spans)
            sub_b = renderer.html_submission(score.sub_b, file_to_spans, ignored_spans)

            all_html_fragments = [frag for file in sub_a.files for frag in file.fragments] +\
                                 [frag for file in sub_b.files for frag in file.fragments]
            json_data = renderer.data(all_html_fragments, groups, ignored_spans)

            data_content = self._read_file(pathlib.Path(__file__).absolute().parent / "templates/data.html")
            data_template = jinja2.Template(data_content, autoescape=jinja2.select_autoescape(enabled_extensions=("html",)))
            data_rendered_html = data_template.render(data=[json_data])

            match_content = self._read_file(pathlib.Path(__file__).absolute().parent / "templates/match.html")
            match_template = jinja2.Template(match_content, autoescape=jinja2.select_autoescape(enabled_extensions=("html",)))
            match_rendered_html = match_template.render(sub_a=sub_a, sub_b=sub_b)

            page_content = self._read_file(pathlib.Path(__file__).absolute().parent / "templates/match_page.html")
            page_template = jinja2.Template(page_content, autoescape=jinja2.select_autoescape(enabled_extensions=("html",)))
            page_rendered_html = page_template.render(match=match_rendered_html,
                                            data=data_rendered_html,
                                            js=self.js,
                                            css=self.css)

            return match_id, page_rendered_html

    @staticmethod
    def _read_file(fname):
        with open(fname) as f:
            return f.read()

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


class _Renderer:
    def __init__(self):
        self._frag_id_counter = -1
        self._span_id_store = IdStore()
        self._group_id_store = IdStore()

    def frag_id(self, frag):
        self._frag_id_counter += 1
        return f"frag{self._frag_id_counter}"

    def group_id(self, group):
        return self._group_id_store[group]

    def span_id(self, span):
        return self._span_id_store[span]

    def html_fragments(self, file, spans, ignored_spans):
        frags = []
        for fragment in fragmentize(file, spans):
            frag_id = self.frag_id(fragment)
            is_ignored = any(span in ignored_spans for span in fragment.spans)
            is_grouped = any(span not in ignored_spans for span in fragment.spans)
            frags.append(HTML_Fragment(frag_id, fragment.content, is_ignored, is_grouped, fragment.spans))
        return frags

    def html_files(self, submission, file_to_spans, ignored_spans):
        files = []
        for file in submission.files:
            spans = file_to_spans[file]
            html_frags = self.html_fragments(file, spans, ignored_spans)

            # Count number of chars
            num_chars = 0
            num_chars_matched = 0
            for frag in html_frags:
                if not frag.is_ignored:
                    num_frag_chars = sum(len(line) for line in frag.content)
                    num_chars += num_frag_chars
                    if frag.is_grouped:
                        num_chars_matched += num_frag_chars

            files.append(HTML_File(str(file.name), html_frags, num_chars_matched, num_chars))
        return files

    def html_submission(self, submission, file_to_spans, ignored_spans):
        html_files = self.html_files(submission, file_to_spans, ignored_spans)
        num_chars_matched = sum(f.num_chars_matched for f in html_files)
        num_chars = sum(f.num_chars for f in html_files)
        return HTML_Submission(str(submission.path), html_files, num_chars_matched, num_chars)

    def data(self, html_fragments, groups, ignored_spans):
        fragment_to_spans = {}
        for fragment in html_fragments:
            if fragment.is_grouped:
                fragment_to_spans[fragment.id] = [self.span_id(span) for span in fragment.spans if span not in ignored_spans]

        span_to_group = {}
        for group in groups:
            group_id = self.group_id(group)
            for span in group.spans:
                span_to_group[self.span_id(span)] = group_id

        return Data(span_to_group, fragment_to_spans)


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
