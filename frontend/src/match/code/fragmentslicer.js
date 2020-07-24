function slice(code, spans) {
    const slicingMarks = [];
    spans.forEach(span => {
        slicingMarks.push(span.start);
        slicingMarks.push(span.end);
    });

    slicingMarks.push(0);
    slicingMarks.push(code.length);

    slicingMarks.sort((a, b) => a - b).filter((item, pos, array) => !pos || item !== array[pos - 1]);

    let fragments = [];
    for (let i = 0; i < slicingMarks.length - 1; i++) {
        const fragment = code.substring(slicingMarks[i], slicingMarks[i + 1]);
        fragments.push(fragment);
    }

    return fragments;
}


function createFragments(file, pass) {
    let spans = [];
    pass.groups.forEach(group => {
        group.forEach(span => {
            if (span.file_id === file.id) {
                spans.push(span);
            }
        })
    });

    let ignored = pass.ignored_spans.filter(span => span.file_id === file.id);

    return slice(file.content, spans.concat(ignored));
}


export default createFragments;
