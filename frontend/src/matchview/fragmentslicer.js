function slice(code, spans) {
    const slicing_marks = [];
    spans.forEach(span => {
        slicing_marks.push(span.start);
        slicing_marks.push(span.end);
    });

    slicing_marks.push(0);
    slicing_marks.push(code.length);

    slicing_marks.sort((a, b) => a - b).filter((item, pos, array) => !pos || item !== array[pos - 1]);

    let fragments = [];
    for (let i = 0; i < slicing_marks.length - 1; i++) {
        const fragment = code.substring(slicing_marks[i], slicing_marks[i + 1]);
        fragments.push(fragment);
    }

    return fragments;
}

export default slice;
