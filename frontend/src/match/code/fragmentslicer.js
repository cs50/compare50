class Fragment {
    constructor(file, start, end) {
        this.fileId = file.id;
        this.start = start;
        this.end = end;
        this.text = file.content.substring(start, end);
    }
}


function slice(file, spans) {
    let slicingMarks = [];
    spans.forEach(span => {
        slicingMarks.push(span.start);
        slicingMarks.push(span.end);
    });

    slicingMarks.push(0);
    slicingMarks.push(file.content.length);

    slicingMarks = Array.from(new Set(slicingMarks));

    slicingMarks.sort((a, b) => a - b);

    let fragments = [];
    for (let i = 0; i < slicingMarks.length - 1; i++) {
        fragments.push(new Fragment(file, slicingMarks[i], slicingMarks[i + 1]));
    }

    return fragments;
}


// Spans of individual spaces are never relevant for the view,
// but do cause many more fragments to be created.
// For performance reasons, this filters out any spans containing just a space.
function filterIgnoredWhitespaceSpans(file, spans) {
    return spans.filter(span => {
        if (span.end - span.start === 1 && file.content[span.start] === " ") {
            return false;
        }
        return true;
    });
}


function createFragments(file, spans) {
    return slice(file, filterIgnoredWhitespaceSpans(file, spans));
}


export default createFragments;
