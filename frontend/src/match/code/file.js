import React, {useState, useRef, useEffect} from 'react';

import "./file.css";


function File(props) {
    const [visibilityRef, entry] = useIntersect({
        threshold: Array.from(Array(100).keys(), i => i / 100),
    });

    useEffect(() => {
        props.updateFileVisibility(props.file.name, entry.intersectionRatio);
    });

    // Keep track of whether a line of code starts on a newline (necessary for line numbers through css)
    let starts_on_newline = true;

    const renderFragment = (frag, frag_index) => {
        // Break up the fragments into lines (keep the newline)
        const lines = frag.split(/(?<=\n)/g);

        // Create a code element for each line
        const code_elems = lines.map((line, line_index) => {
            const code_elem = (
                <code
                    key={`line_${props.file.id}_${frag_index}_${line_index}`}
                    className={starts_on_newline ? "newline" : ""}
                >
                    {line}
                </code>
            );

            starts_on_newline = line.endsWith("\n");

            return code_elem;
        });

        return (
            <span key={`fragment_${props.file.id}_${frag_index}`}>
                {code_elems}
            </span>
        )
    }

    return (
        <>
            <h4> {props.file.name} <span>({props.file.percentage}%)</span></h4>
            <pre ref={visibilityRef} className={props.softWrap ? "softwrap" : ""}>
                {props.file.fragments.map(renderFragment)}
            </pre>
        </>
    )
}


// https://medium.com/the-non-traditional-developer/how-to-use-an-intersectionobserver-in-a-react-hook-9fb061ac6cb5
const useIntersect = ({root=null, rootMargin, threshold=0}) => {
    const [entry, updateEntry] = useState({});
    const [node, setNode] = useState(null);

    const observer = useRef(
        new window.IntersectionObserver(([entry]) => updateEntry(entry), {
        root,
        rootMargin,
        threshold
    }));

    useEffect(() => {
        const { current: currentObserver } = observer;
        currentObserver.disconnect();

        if (node) {
            currentObserver.observe(node);
        }

        return () => currentObserver.disconnect();
    }, [node]);

    return [setNode, entry];
};


export default File
