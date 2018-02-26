# script with example celery task
import celery_app
import time

from celery.result import AsyncResult

# run task asynchronously
task = celery_app.greet.delay("Thomas")

# access task state and other fields (e.g., id, result)
print(f"STATE: {task.state}")

# given a task id you can still access these fields by instantiating a result
print("Fetching task metadata using task id ...")
same_task = AsyncResult(task.id)
print(f"STATE: {same_task.state}")

while same_task.state != "SUCCESS":
    time.sleep(1)

print(same_task.result)
