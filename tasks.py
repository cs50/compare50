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

@app.task(bind=True)
def compare_task(self):
    print(f"starting compare task for {self.request.id}")
    parent = os.path.join(gettempdir(), self.request.id)

    # find directories where files were saved
    submission_dir = os.path.join(parent, "submissions")
    distro_dir = os.path.join(parent, "distros")
    archive_dir = os.path.join(parent, "archives")

    # get submission lists
    submissions = walk_submissions(submission_dir)
    distros = walk(distro_dir) if os.path.exists(distro_dir) else []
    archives = walk_submissions(archive_dir) if os.path.exists(archive_dir) else []

    results = compare(submissions, distros, archives)

    # cannot use tuples as keys or sets in json, so do translation
    results = [
        {
            "files": files,
            "passes": {
                name: (score, [
                    (
                        [
                            {
                                "file": files[0].index(f.file),
                                "start": f.start,
                                "stop": f.stop
                            }
                        for f in a_frags
                        ],
                        [
                            {
                                "file": files[1].index(f.file),
                                "start": f.start,
                                "stop": f.stop
                            }
                        for f in b_frags
                        ]
                    )
                    for a_frags, b_frags in frag_pairs
                ])
                for name, (score, frag_pairs) in passes.items()
            }
        }
        for files, passes in results.items()
    ]

    result_path = os.path.join(parent, "results.json")
    with open(result_path, "w") as f:
        f.write(json.dumps(results))
    print(f"Finished {self.request.id}!")
    return result_path
