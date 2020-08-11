import React, {useState, useRef, useEffect, useCallback} from 'react';
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
            {[props.match.filesA(), props.match.filesB()].map((files, i) =>
                <div key={`side_${i}`} style={{"height":"100%", "margin":0, "float":"left"}}>
                    <Side
                        pass={props.pass}
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

    const ref = useRef(null);
    const scrollToCallback = useCallback(domElement => scrollTo(domElement, ref.current, props.setInteractionBlocked), [ref, props.setInteractionBlocked]);

    return (
        <div className="column-box">
            <div className="row auto" style={{
                "height":props.height,
                "lineHeight":props.height
            }}>
                <StatusBar
                    filepath="looooooooooooooooooooooooooooooooooooooooooooong/file/path/to/submission_a"
                    percentage={70}
                    file={fileInView}
                    height={props.topHeight}/>
            </div>
            <div ref={ref} className="scrollable-side row fill" style={{"overflow":"scroll"}}>
                <div style={{"paddingLeft":".5em"}}>
                    {props.files.map(file =>
                        <File
                            key={file.name}
                            file={file}
                            spanManager={props.spanManager}
                            percentage={20}
                            softWrap={props.globalState.softWrap}
                            hideIgnored={props.globalState.hideIgnored}
                            showWhiteSpace={props.globalState.showWhiteSpace}
                            updateFileVisibility={updateFileVisibility}
                            scrollTo={scrollToCallback}
                            interactionBlocked={props.interactionBlocked}
                        />
                    )}
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
                "overflow":"scroll",
                "marginLeft":"5px",
                "marginRight":"5px"
            }}>
                {props.filepath}
            </div>
            <div className="row auto" style={{
                "width":"4em",
                "textAlign":"center"
            }}>
                {`${props.percentage}%`}
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
    let duration = 300;

    let start = scrollable.scrollTop;
    let change = to - start;
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
