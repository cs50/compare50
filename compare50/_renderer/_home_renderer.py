import jinja2

from ._renderer import STATIC, TEMPLATES


def render_home(sub_pair_to_results):
    subs_dict = submissions_as_dict(get_submissions(sub_pair_to_results))
    links = links_as_dict(sub_pair_to_results)

    with open(TEMPLATES / "home.html") as f:
        template = jinja2.Template(f.read(), autoescape=jinja2.select_autoescape(enabled_extensions=("html",)))
    rendered_data = template.render(SUBMISSIONS=subs_dict, LINKS=links)

    with open(STATIC / "home.html") as f:
        home_page = f.read()

    return rendered_data + "\n" + home_page


def submissions_as_dict(submissions):
    return {sub.id: {
        "id": sub.id,
        "path": str(sub.path),
        "isArchive": sub.is_archive
    } for sub in submissions}


def links_as_dict(sub_pair_to_results):
    max_score = max((results[0].score.score for results in sub_pair_to_results.values()))
    normalize_score = lambda score: score / max_score * 10

    links = []

    for i, ((sub_a, sub_b), results) in enumerate(sub_pair_to_results.items()):
        score = results[0].score.score

        links.append({
            "index": i,
            "submissionIdA": sub_a.id,
            "submissionIdB": sub_b.id,
            "score": score,
            "normalized_score": normalize_score(score),
        })

    return links


def get_submissions(sub_pair_to_results):
    submissions = set()
    for sub_a, sub_b in sub_pair_to_results:
        submissions.add(sub_a)
        submissions.add(sub_b)
    return submissions
