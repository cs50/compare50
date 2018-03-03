import os
from celery import Celery
from compare import compare

app = Celery("tasks",
             backend="db+mysql://{}:{}@{}/{}/celerydb".format(
                 os.environ["MYSQL_USERNAME"],
                 os.environ["MYSQL_PASSWORD"],
                 os.environ["MYSQL_HOST"],
                 os.environ["MYSQL_DATABASE"]),
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
    result_path = os.path.join(parent, "results.json")
    with open(result_path, "w") as f:
        f.write(jsonify_results)
    print(f"Finished {self.request.id}!")
    return result_path
