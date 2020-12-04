import collections
import pathlib
import pkg_resources

STATIC = pathlib.Path(pkg_resources.resource_filename("compare50._renderer", "static"))
TEMPLATES = pathlib.Path(pkg_resources.resource_filename("compare50._renderer", "templates"))

from .. import _api
from ._home_renderer import render_home
from ._match_renderer import render_match


class Cluster:
    def __init__(self, sub_pair_to_results):
        self._sub_pair_to_results = sub_pair_to_results
        self.links = set(sub_pair_to_results.keys())

        self.submissions = set()
        for sub_a, sub_b in sub_pair_to_results:
            self.submissions.add(sub_a)
            self.submissions.add(sub_b)
    

    def submissions_as_dict(self):
        return {sub.id: {
            "id": sub.id,
            "path": str(sub.path),
            "isArchive": sub.is_archive
        } for sub in self.submissions}


    def links_as_dict(self):
        max_score = max((results[0].score.score for results in self._sub_pair_to_results.values()))
        normalize_score = lambda score: score / max_score * 10

        links = []

        for i, ((sub_a, sub_b), results) in enumerate(self._sub_pair_to_results.items()):
            score = results[0].score.score

            links.append({
                "index": i,
                "submissionIdA": sub_a.id,
                "submissionIdB": sub_b.id,
                "score": score,
                "normalized_score": normalize_score(score),
            })

        return links


    def get_subcluster(self, submission):
        """Get the cluster of submissions directly or indirectly linked with submission"""

        # Build a dict to quickly access links from either end
        links_dict = collections.defaultdict(list)
        for a, b in self.links:
            links_dict[a].append(b)
            links_dict[b].append(a)

        # Build the cluster with Depth-First-Search
        cluster_links = set()
        seen_subs = {submission}
        untraversed_subs = [submission]
        while untraversed_subs:
            untraversed_sub = untraversed_subs.pop()
            
            for sub in links_dict[untraversed_sub]:
                if sub not in seen_subs:
                    seen_subs.add(sub)
                    untraversed_subs.append(sub)
                
                cluster_links.add((untraversed_sub, sub))

        # Build the cluster, each original link + its result
        cluster = {}
        for link in cluster_links:
            if link in self._sub_pair_to_results:
                cluster[link] = self._sub_pair_to_results[link]
        
        return Cluster(cluster)


def render(pass_to_results, dest):
    bar = _api.get_progress_bar()
    dest = pathlib.Path(dest)

    # Create a cluster of submissions
    sub_pair_to_results = collections.defaultdict(list)
    for results in pass_to_results.values():
        for result in results:
            sub_pair_to_results[(result.sub_a, result.sub_b)].append(result)
    cluster = Cluster(sub_pair_to_results)

    # Create the directory if it does not yet exist
    dest.mkdir(exist_ok=True)

    # Render matches
    for i, ((sub_a, sub_b), results) in enumerate(sub_pair_to_results.items()):
        subcluster = cluster.get_subcluster(sub_a)

        metadata = {
            "index": i + 1,
            "numberOfMatches": len(sub_pair_to_results)
        }

        match = render_match(sub_a, sub_b, results, subcluster, metadata)

        with open(dest / f"match_{i + 1}.html", "w") as f:
            f.write(match)

    # Render home page
    home = render_home(cluster)
    home_path = dest / "home.html"
    with open(home_path, "w") as f:
        f.write(home)

    return home_path

