from celery import Celery

# arguments are:
#    app name
#    backend (mysql in this case but can be different http://docs.celeryproject.org/en/latest/userguide/tasks.html#task-result-backends
#    url for message broker
#    scripts containing celery tasks
app = Celery(
    "celery_app",
    backend="db+mysql://root@localhost/celerydb",
    broker="amqp://localhost",
    # include=["<moudle containing tasks>", ...]
)

# this decorator indicates following function is celery task
# it can take parameters (e.g., to specify different base class for task,
# change task name, binding task, etc
# http://docs.celeryproject.org/en/latest/userguide/tasks.html
@app.task
def greet(name):
    return f"hello, {name}"
