import React, {useState, useRef, useEffect, useMemo} from 'react';
import createFragments from './fragmentslicer'

import "../matchview.css"
import "./file.css";

// function useTraceUpdate(props) {
//   const prev = useRef(props);
//   useEffect(() => {
//     const changedProps = Object.entries(props).reduce((ps, [k, v]) => {
//       if (prev.current[k] !== v) {
//         ps[k] = [prev.current[k], v];
//       }
//       return ps;
//     }, {});
//     if (Object.keys(changedProps).length > 0) {
//       console.log('Changed props:', changedProps);
//     }
//     prev.current = props;
//   });
// }

function File(props) {
    const [visibilityRef, entry] = useIntersect({
        threshold: Array.from(Array(100).keys(), i => i / 100),
    });

    useEffect(() => {
        props.updateFileVisibility(props.file.name, entry.intersectionRatio);
    });

    const fragments = useMemo(() => {
        const fromFile = span => span.fileId === props.file.id;
        const spans = props.spanManager.spans.filter(fromFile);
        const ignoredSpans = props.spanManager.ignoredSpans.filter(fromFile);
        const allSpans = spans.concat(ignoredSpans);
        return createFragments(props.file, allSpans)
    }, [props.file.id, props.spanManager.spans]);

    // Keep track of whether a line of code starts on a newline (necessary for line numbers through css)
    let onNewline = true;

    const fragmentElems = fragments.map((frag, i) => {
        const id = `frag_${props.file.id}_${frag.start}`;
        const fragElem = <Fragment
                            key={id}
                            fragment={frag}
                            fileId={props.file.id}
                            id={id}
                            onNewline={onNewline}
                            hideIgnored={props.hideIgnored}
                            showWhiteSpace={props.showWhiteSpace}
                            scrollTo={props.scrollTo}
                            spanManager={props.spanManager}
                            interactionBlocked={props.interactionBlocked}
        />
        onNewline = frag.text.endsWith("\n");
        return fragElem;
    });

    return (
        <>
            <h4> {props.file.name} <span>({props.percentage}%)</span></h4>
            <pre ref={visibilityRef} className={(props.softWrap ? "softwrap" : "") + " monospace-text"}>
                {(fragmentElems)}
            </pre>
        </>
    )
}


function Fragment(props) {
    // Break up the fragments into lines (keep the newline)
    const lines = props.fragment.text.split(/(?<=\n)/g);

    const ref = useRef(null);

    const isHighlighted = props.spanManager.isHighlighted(props.fragment);

    useEffect(() => {
        // If this fragment is highlighted, and it's the first in its span, scroll to it
        if (isHighlighted && props.spanManager.isFirstInHighlightedSpan(props.fragment)) {
            props.scrollTo(ref.current);
        }
    })

    let className = getClassName(props.fragment, props.spanManager, props.hideIgnored);

    const hasMouseOvers = !props.interactionBlocked && props.spanManager.isGrouped(props.fragment);

    return (
        <span
            ref={ref}
            className={className}
            key={props.id}
            onMouseEnter={hasMouseOvers ? event => props.spanManager.activate(props.fragment) : undefined}
            onMouseDown={hasMouseOvers ? event => {
                // Prevent text selection when clicking on highlighted fragments
                if (props.spanManager.isHighlighted(props.fragment)) {
                    event.preventDefault();
                }
            } : undefined}
            onMouseUp={hasMouseOvers ? event => {
                props.spanManager.select(props.fragment);
            } : undefined}
        >
            {lines.map((line, lineIndex) => {
                const onNewline = props.onNewline || lineIndex > 0

                // If starting on a newline, make the leading whitespace visible
                if (onNewline && props.showWhiteSpace) {
                    line = replaceLeadingWhitespace(line);
                }

                return (
                    <code
                        key={`code_${props.id}_${lineIndex}`}
                        className={onNewline ? "newline" : ""}
                    >
                        {line}
                    </code>
                )
            })}
        </span>
    )
}


function replaceLeadingWhitespace(line) {
    let newLine = ""

    for (let i = 0; i < line.length; i++) {
        if (line[i] === " ") {
            newLine += ".";
        }
        else if (line[i] === "\t") {
            newLine += "____";
        }
        else {
            newLine += line.slice(i);
            break;
        }
    }

    return newLine;
}


function getClassName(fragment, spanManager, hideIgnored) {
    const classNames = [];
    if (spanManager.isIgnored(fragment)) {
        if (hideIgnored) {
            classNames.push("invisible-span");
        } else {
            classNames.push("ignored-span");
        }
    }

    if (spanManager.isHighlighted(fragment)) {
        classNames.push("highlighted-span");
    }
    else if (spanManager.isActive(fragment)) {
        classNames.push("active-span");
    }
    else if (spanManager.isSelected(fragment)) {
        classNames.push("selected-span");
    }
    else if (spanManager.isGrouped(fragment)) {
        classNames.push("grouped-span");
    }

    return classNames.join(" ");
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
