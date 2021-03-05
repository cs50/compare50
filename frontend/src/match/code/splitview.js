import React, {useState, useRef, useEffect, useCallback, useMemo} from 'react';
import Split from 'react-split';

import File from './file'

import '../matchview.css';
import '../../split.css';


function SplitView(props) {
    const [interactionBlocked, setInteractionBlocked] = useState(false);

    return (
        <Split
            sizes={[50, 50]}
            gutterSize={10}
            gutterAlign="center"
            snapOffset={30}
            dragInterval={1}
            direction="horizontal"
            cursor="col-resize"
            style={{
                "height":"100%"
            }}
        >
            {[[props.match.filesA(), props.match.subA], [props.match.filesB(), props.match.subB]].map(([files, sub], i) =>
                <div key={`side_${i}`} style={{"height":"100%", "margin":0, "float":"left"}}>
                    <Side
                        pass={props.pass}
                        submission={sub}
                        files={files}
                        interactionBlocked={interactionBlocked}
                        setInteractionBlocked={setInteractionBlocked}
                        spanManager={props.spanManager}
                        globalState={props.globalState}
                        topHeight={props.topHeight}
                    />
                </div>
            )}
        </Split>
    )
}


function Side(props) {
    const [fileInView, updateFileVisibility] = useMax(props.files.map(file => file.name));

    const [submissionCoverage, fileCoverages] = useCoverages(props.files, props.spanManager.spans);

    const ref = useRef(null);

    const scrollToCallback = useScroll(ref, props.spanManager, props.setInteractionBlocked);

    return (
        <div className="column-box">
            <div className="row auto" style={{
                "height":props.height,
                "lineHeight":props.height
            }}>
                <StatusBar
                    filepath={props.submission.name}
                    percentage={submissionCoverage * 100}
                    file={fileInView}
                    height={props.topHeight}/>
            </div>
            <div ref={ref} className="scrollable-side row fill" style={{"overflow":"scroll"}}>
                <div style={{"paddingLeft":".5em"}}>
                    {props.files.map((file, i) =>
                        <File
                            key={file.name}
                            file={file}
                            spanManager={props.spanManager}
                            percentage={fileCoverages[i] * 100}
                            softWrap={props.globalState.softWrap}
                            hideIgnored={props.globalState.hideIgnored}
                            showWhiteSpace={props.globalState.showWhiteSpace}
                            updateFileVisibility={updateFileVisibility}
                            scrollTo={scrollToCallback}
                            interactionBlocked={props.interactionBlocked}
                        />
                    )}
                    <div style={{"height":"75vh"}}></div>
                </div>
            </div>
        </div>
    )
}


function StatusBar(props) {
    const filepathRef = useRef(null);

    useEffect(() => {
        filepathRef.current.scrollLeft = filepathRef.current.scrollWidth;
    });

    return (
        <div className="row-box" style={{
            "fontWeight":"bold",
            "height":props.height,
            "lineHeight":props.height
        }}>
            <div ref={filepathRef} className="row fill" style={{
                "overflowY":"hidden",
                "overflowX":"auto",
                "marginRight":"5px",
                "paddingLeft":".5em"
            }}>
                {props.filepath}
            </div>
            <div className="row auto" style={{
                "width":"4em",
                "textAlign":"center"
            }}>
                {`${props.percentage.toFixed(0)}%`}
            </div>
            <div className="row auto" style={{
                "width":"10em",
                "textAlign":"center"
            }}>
                {props.file}
            </div>
        </div>
    )
}


function useMax(items, initial=null) {
    if (initial === null) {
        initial = items[0];
    }

    const [item, setItem] = useState(initial);

    const values = useRef(items.reduce((acc, item) => {
        acc[item] = 0;
        return acc;
    }, {}));

    // Callback for when the value of an item changes
    const update = useCallback((item, value) => {
        values.current[item] = value;

        // Find the item with the highest value
        let maxItem = item;
        let maxValue = 0;
        Object.entries(values.current).forEach(([item, value]) => {
            if (value > maxValue) {
                maxItem = item;
                maxValue = value;
            }
        });

        // If the item with the highest value is different from the last, update maxItem
        if (item !== maxItem) {
            setItem(maxItem);
        }
    }, []);

    return [item, update];
}


function useCoverages(files, spans) {
    const compute = () => {
        spans = spans.filter(span => !span.isIgnored);

        let totalNumMatchedChars = 0;

        const filesCoverages = files.map(file => {
            const numMatchedChars = spans.reduce((acc, span) => acc + (span.fileId === file.id ? span.end - span.start : 0), 0);
            totalNumMatchedChars += numMatchedChars;
            return (numMatchedChars / file.content.length);
        });

        const totalNumChars = files.reduce((acc, file) => acc + file.content.length, 0)

        const submissionCoverage = totalNumChars === 0 ? 0 : totalNumMatchedChars / totalNumChars;

        return [submissionCoverage, filesCoverages];
    }

    return useMemo(compute, [files, spans]);
}


function useScroll(scrollableRef, spanManager, setInteractionBlocked) {
    const didScroll = useRef(false);

    const highlightedSpans = spanManager.highlightedSpans().map(span => span.id);
    const prevHighlightedSpans = useRef(highlightedSpans);

    const didHighlightChange = () => {
        if (highlightedSpans.length !== prevHighlightedSpans.current.length) {
            return true;
        }

        for (let i = 0; i < highlightedSpans.length; i++) {
            if (highlightedSpans[i] !== prevHighlightedSpans.current[i]) {
                return true;
            }
        }
        return false;
    }

    // In case the highlighted spans changed, re-enable scrolling
    if (didHighlightChange()) {
        didScroll.current = false;
        prevHighlightedSpans.current = highlightedSpans;
    }

    const scrollToCallback = useCallback(domElement => {
        if (didScroll.current) {
            return;
        }
        didScroll.current = true;
        scrollTo(domElement, scrollableRef.current, setInteractionBlocked);
    }, [scrollableRef, setInteractionBlocked]);

    return scrollToCallback;
}


function findPos(domElement) {
    let obj = domElement;
    let curtop = 0;
    if (obj.offsetParent) {
        do {
            curtop += obj.offsetTop;
            obj = obj.offsetParent;
        } while (obj);
    }
    return curtop;
}


// Custom implementation/hack of element.scrollIntoView();
// Because safari does not support smooth scrolling @ July 27 2018
// Update @ July 29 2020, still no smooth scrolling in Safari
// Feel free to replace once it does:
//     this.dom_element.scrollIntoView({"behavior":"smooth"});
// Also see: https://github.com/iamdustan/smoothscroll
// Credits: https://gist.github.com/andjosh/6764939
function scrollTo(domElement, scrollable=document, setInteractionBlock=block => {}, offset=200) {
    let easeInOutQuad = (t, b, c, d) => {
        t /= d / 2;
        if (t < 1) return c / 2 * t * t + b;
        t--;
        return -c / 2 * (t * (t - 2) - 1) + b;
    };

    let to = findPos(domElement) - offset;

    let start = scrollable.scrollTop;
    let change = to - start;
    let duration = Math.min(300, Math.max(Math.abs(change), 40));
    let currentTime = 0;
    let increment = 20;

    let animateScroll = () => {
        currentTime += increment;
        let val = easeInOutQuad(currentTime, start, change, duration);

        scrollable.scrollTop = val;
        if (currentTime < duration) {
            setTimeout(animateScroll, increment);
        }
        else {
            setInteractionBlock(false);
        }
    };

    setInteractionBlock(true);
    animateScroll();
}


export default SplitView
