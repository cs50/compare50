import jinja2

from ._renderer import STATIC, TEMPLATES


def render_home(cluster):
    with open(TEMPLATES / "home.html") as f:
        template = jinja2.Template(f.read(), autoescape=jinja2.select_autoescape(enabled_extensions=("html",)))
    rendered_data = template.render(SUBMISSIONS=cluster.submissions_as_dict(), LINKS=cluster.links_as_dict())

    with open(STATIC / "home.html") as f:
        home_page = f.read()

    return rendered_data + "\n" + home_page


