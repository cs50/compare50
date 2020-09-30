import collections
import pathlib
import pkg_resources

STATIC = pathlib.Path(pkg_resources.resource_filename("compare50._renderer", "static"))
TEMPLATES = pathlib.Path(pkg_resources.resource_filename("compare50._renderer", "templates"))

from .. import _api
from ._home_renderer import render_home
from ._match_renderer import render_match


def render(pass_to_results, dest):
    bar = _api.get_progress_bar()
    dest = pathlib.Path(dest)

    sub_pair_to_results = collections.defaultdict(list)
    for results in pass_to_results.values():
        for result in results:
            sub_pair_to_results[(result.sub_a, result.sub_b)].append(result)

    dest.mkdir(exist_ok=True)

    # Render matches
    for i, ((sub_a, sub_b), results) in enumerate(sub_pair_to_results.items()):
        match = render_match(sub_a, sub_b, results)

        with open(dest / f"match_{i}.html", "w") as f:
            f.write(match)

    # Render home page
    home = render_home(sub_pair_to_results)
    home_path = dest / "home.html"
    with open(home_path, "w") as f:
        f.write(home)

    return home_path
