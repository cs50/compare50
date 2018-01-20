# Compare50

## Comparison engine
The entry point to the comparison engine is the `compare1 function in
compare.py.

`compare(submissions, distro=[], corpus=[])`

- `submissions`: a list of tuples, where each tuple contains the file
  paths comprising a single student submission.
- `distro`: a tuple of file paths comprising the distribution code to
  be excluded from the comparison.
- `corpus`: a list of tuples, where each tuple contains the file paths
  comprising a single student submission.

All submissions in `submissions` are compared with every other
submission in `submissions` and with every submission in
`corpus`. Submissions in `corpus` are not compared with each other.

`compare` returns a structure with the following layout:

- dict mapping pair of submission file tuples to
  - dict mapping pass name to pair of
    - similarity score for pass, and
    - list of pairs corresponding to fragments, containing
      - set of `Span` containing fragment in submission A
      - set of `Span` containing fragment in submission B

Inner dict entries for submission pair + pass combinations that did
not find any similarities may be omitted.

A `Span` represents a contiguous span of characters in a file, and has
the following properties:
- `file`: the path of the file this span is within
- `start`: the index of the first character in the span
- `stop`: the index one past the end of the span

(TODO: user-supplied configurations)

## Determinism
Fingerprint hashing is currently done using Python's built in `hash`
function. Python randomly salts this hash function on startup, so
different runs on the same input may not catch the same similar
fragments, report the same similarity scores, or produce the same
rankings. If deterministic scoring is desired, set the environment
variable PYTHONHASHSEED to some constant so the hash function will
always be salted the same way.

If fingerprint hashes are ever serialized, we will need to switch to a
deterministic hash function, since even constantly-salted `hash` could
change in between Python versions.
