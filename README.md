# Compare50

### Features

## JSON API

## Design

Workflow overview

### Uploads

Describe file format

### Passes

#### Preprocessors

#### Comparators

### Fragments

## Adding Preprocessors and Comparators

## Notes

### Determinism
Fingerprint hashing is currently done using Python's built in `hash`
function. Python randomly salts this hash function on startup, so
different runs on the same input may not catch the same similar
fragments, report the same similarity scores, or produce the same
rankings. If deterministic scoring is desired, set the environment
variable PYTHONHASHSEED to some constant so the hash function will
always be salted the same way. A better solution would be to find a
fast, deterministic hash function to use instead of `hash`.

## Web App Notes
Separate submissions in *Submissions* and *Archives* must be in
separate directories, even they consist of a single file. For each of
these categories, all submissions must either share a parent directory
or be submitted individually.

```
FLASK_APP=application.py flask db init
vim migrations/alembic.ini 
FLASK_APP=application.py flask db migrate
FLASK_APP=application.py flask db upgrade
```

## TODO

* Disallow identical names in same dir.
* Add support for drag-and-drop (with relative paths).
* CLI
* Add error handling so that files are deleted in event of failure.
* Return URL with https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Content-Location, not 302.
