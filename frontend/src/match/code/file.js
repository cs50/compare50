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
    let onNewline = true;

    const fragmentElems = props.file.fragments.map((frag, i) => {
        const id = `fragment_${props.file.id}_${i}`;
        const fragElem = <Fragment key={id} fragment={frag} id={id} onNewline={onNewline}/>
        onNewline = frag.endsWith("\n");
        return fragElem;
    })

    return (
        <>
            <h4> {props.file.name} <span>({props.file.percentage}%)</span></h4>
            <pre ref={visibilityRef} className={props.softWrap ? "softwrap" : ""}>
                {(fragmentElems)}
            </pre>
        </>
    )
}


function Fragment(props) {
    const [hovering, setHovering] = useState(false);

    // Break up the fragments into lines (keep the newline)
    const lines = props.fragment.split(/(?<=\n)/g);

    return (
        <span
            className={hovering ? "active-match" : ""}
            key={props.id}
            onMouseEnter={event => setHovering(true)}
            onMouseLeave={event => setHovering(false)}
        >
            {lines.map((line, lineIndex) =>
                <code
                    key={`code_${props.id}_${lineIndex}`}
                    className={props.onNewline || lineIndex > 0 ? "newline" : ""}
                >
                    {line}
                </code>
            )}
        </span>
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
