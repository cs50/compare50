import collections
import glob
import json
import os
import pathlib
import pkg_resources
import shutil

import attr
import jinja2

from .. import _api
from .._data import IdStore

STATIC = pathlib.Path(pkg_resources.resource_filename("compare50._renderer", "static"))
TEMPLATES = pathlib.Path(pkg_resources.resource_filename("compare50._renderer", "templates"))


def file_as_dict(file):
    return {
        "id": file.id,
        "name": str(file.name),
        "language": file.lexer().name,
        "content": file.read()
    }

def files_as_dict(submission):
    return {
        "id": submission.id,
        "name": str(submission.path),
        "isArchive": submission.is_archive,
        "files": [file_as_dict(file) for file in submission.files]
    }

def span_as_dict(span, span_id_store, ignored=False):
    return {
        "id": span_id_store[span],
        "subId": span.file.submission.id,
        "fileId": span.file.id,
        "start": span.start,
        "end": span.end,
        "ignored": ignored
    }


def pass_as_dict(result, span_id_store, group_id_store):
    spans = []
    groups = []

    for group in result.groups:
        group_data = {
            "id": group_id_store[group],
            "spans": []
        }

        for span in group.spans:
            group_data["spans"].append(span_id_store[span])
            spans.append(span_as_dict(span, span_id_store))

        groups.append(group_data)

    for span in result.ignored_spans:
        spans.append(span_as_dict(span, span_id_store, ignored=True))

    return {
        "name": result.pass_.__name__,
        "docs": result.pass_.__doc__,
        "score": result.score.score,
        "spans": spans,
        "groups": groups
    }


def render(pass_to_results, dest):
    bar = _api.get_progress_bar()
    dest = pathlib.Path(dest)

    sub_pair_to_results = collections.defaultdict(list)
    for results in pass_to_results.values():
        for result in results:
            sub_pair_to_results[(result.sub_a, result.sub_b)].append(result)

    dest.mkdir(exist_ok=True)
    for i, ((sub_a, sub_b), results) in enumerate(sub_pair_to_results.items()):
        match = render_match(sub_a, sub_b, results)
        print(match)
        with open(dest / f"match_{i}.html", "w") as f:
            f.write(match)

    # TODO render index page
    return


def render_match(sub_a, sub_b, results):
    files_a = files_as_dict(sub_a)
    files_b = files_as_dict(sub_b)

    span_id_store = IdStore()
    group_id_store = IdStore()

    passes = [pass_as_dict(result, span_id_store, group_id_store) for result in results]

    with open(TEMPLATES / "match.html") as f:
        template = jinja2.Template(f.read(), autoescape=jinja2.select_autoescape(enabled_extensions=("html",)))

    with open(STATIC / "match.html") as f:
        match_page = f.read()

    rendered_data =  template.render(match_page=match_page, FILES_A=files_a, FILES_B=files_b, PASSES=passes)

    return rendered_data + "\n" + match_page
