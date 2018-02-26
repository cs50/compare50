# celery dameon in Docker

## Building

```
# cd into this directory
$ docker build -t repo/name:tag .
```

`repo` and `tag` are optional.

## Running:

```
$ docker run -it --rm repo/name:tag
```

This starts a docker container whose initial commands are:
 . Starting mysql server.
 . Creating mysql database for celery as a backend for storing task metadata.
 . Starting celery daemon.
 . Starting rabbitmq daemon.
 . Running a python script that calls a task asyncronously and prints its result to stdout.

## Files:

 . `Dockerfile` defines the docker image.
 . `celery_app` a python script containing the celery app, some configuration, and a sample task.
 . `celery_demo` a script that runs a task asynchronously, waits for it to be done, and prints its result.

