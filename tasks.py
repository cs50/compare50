import os
import json

from tempfile import gettempdir, mkstemp
from celery import Celery

from util import walk, walk_submissions
from compare.compare import compare
from compare.util import Span

app = Celery("tasks",
             backend="db+mysql://{}:{}@{}/celerydb".format(
                 os.environ["MYSQL_USERNAME"],
                 os.environ["MYSQL_PASSWORD"],
                 os.environ["MYSQL_HOST"]),
             broker="amqp://localhost")


class ResultEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, set):
            return list(obj)
        if isinstance(obj, Span):
            return [obj.file, obj.start, obj.stop]
        return json.JSONEncoder.default(self, obj)


@app.task(bind=True)
def compare_task(self):
    parent = os.path.join(gettempdir(), self.request.id)

    # find directories where files were saved
    submission_dir = os.path.join(parent, "submissions")
    distro_dir = os.path.join(parent, "distros")
    archive_dir = os.path.join(parent, "archives")

    # get submission lists
    submissions = walk_submissions(submission_dir)
    distros = walk(distro_dir) if os.path.exists(distro_dir) else []
    archives = walk_submissions(archive_dir) if os.path.exists(archive_dir) else []

    files, groups, passes, results = compare(submissions, distros, archives)

    # remove redundancy from file paths
    files = [os.path.relpath(f, parent) for f in files]

    # cannot use tuples as keys in json
    results = [{"subs": sub_pair, "passes": passes}
               for sub_pair, passes in results.items()]
    info = {
        "files": files,
        "groups": groups,
        "passes": passes,
        "results": results
    }
    result_path = os.path.join(parent, "results.json")
    with open(result_path, "w") as f:
        json.dump(info, f, separators=(",", ":"), cls=ResultEncoder)
    return result_path
