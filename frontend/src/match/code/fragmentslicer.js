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

    slicingMarks.sort((a, b) => a - b).filter((item, pos, array) => !pos || item !== array[pos - 1]);

    let fragments = [];
    for (let i = 0; i < slicingMarks.length - 1; i++) {
        fragments.push(new Fragment(file, slicingMarks[i], slicingMarks[i + 1]));
    }

    return fragments;
}


function createFragments(file, spans) {
    return slice(file, spans);
}


export default createFragments;
