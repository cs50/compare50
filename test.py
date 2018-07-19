import winnowing
import pygments
import os
import pathlib
from data import *
import pygments.lexers

class Submission:
    def __init__(self, id, files):
        self.id = id
        self.files = files


class File:
    def __init__(self, id, path):
        self.id = id
        self.path = path

    def preprocess(self, preprocessors):
        """Returns a list of (file, start, end, type, value) tuples created
        using a.  pygments lexer. The lexer is determined by looking
        first at file name then at file contents. If neither
        determines a lexer, a plain text lexer is used. The `type` in
        the output tuple is a pygments Token type.
        """
        file_path = self.path
        with open(file_path, "r")  as file:
            text = file.read()

        # get lexer for this file type
        try:
            lexer = pygments.lexers.get_lexer_for_filename(file_path)
        except pygments.util.ClassNotFound:
            try:
                lexer = pygments.lexers.guess_lexer(text)
            except pygments.util.ClassNotFound:
                lexer = pygments.lexers.special.TextLexer()

        # tokenize file into (start, type, value) tuples
        tokens = list(lexer.get_tokens_unprocessed(text))

        # add file and end index to create Tokens
        tokens.append((len(text),))
        tokens = [Token(start=tokens[i][0], stop=tokens[i+1][0],
                        type=tokens[i][1], val=tokens[i][2])
                  for i in range(len(tokens) - 1)]

        # run preprocessors
        for pp in preprocessors:
            tokens = pp(tokens)
        return list(tokens)


def compare(sub_a, sub_b):
    """Take two submissions and return a tuple of dicts mapping files to
    lists of Fragments.  The id of `sub_a` must be less than that of
    `sub_b`.
    """
    #distro = sub_a.upload.distro

    # map pass ids to MatchResults
    results = {}

    #for p in sub_a.upload.passes:
        #preprocessors, comparator = DEFAULT_CONFIG[p.config]

        #distro_files = p.upload.distro.files if distro else []

    preprocessors = []
    comparator = winnowing.Winnowing(10, 20)

    # keep tokens around for expanding spans
    tokens = {f.id: f.preprocess(preprocessors)
              for f in sub_a.files + sub_b.files} # + distro_files}

    # process files
    a_index = comparator.empty_index()
    b_index = comparator.empty_index()
    distro_index = comparator.empty_index()
    for sub, index in [(sub_a, a_index),
                         (sub_b, b_index)]:
                         #(distro_files, distro_index)]:
        for f in sub.files: # TODO
            index += comparator.index(f.id, sub.id, tokens[f.id], complete=True)

    # perform comparisons
    matches = a_index.compare(b_index)

    return matches

    #     # TODO
    #     if matches:
    #         matches = expand_spans(matches[0], tokens)
    #     else:
    #         # no matches, create empty MatchResult to hold distro code
    #         matches = MatchResult(sub_a.id, sub_b.id, {})
    #     if distro:
    #         # add expanded distro spans to match as group "distro"
    #         for index in a_index, b_index:
    #             distro_match = distro_index.compare(index)
    #             if distro_match:
    #                 distro_match = expand_spans(distro_match[0], tokens)
    #                 distro_spans = [span
    #                                 for spans in distro_match.spans.values()
    #                                 for span in spans
    #                                 if File.query.get(span.file).submission_id != distro.id]
    #                 matches.spans.setdefault("distro", []).extend(distro_spans)
    #
    #     results[p.id] = matches
    #
    # return flatten_spans(results)

c = \
    compare(\
        Submission(0, [File(0, pathlib.Path("files/foo.py").absolute())]),\
        Submission(1, [File(1, pathlib.Path("files/bar.py").absolute())])
    )

print(c)
