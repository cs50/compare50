import React, {useState, useRef, useEffect} from 'react';
import Split from 'react-split';

import API from './api';

import './App.css';
import './split.css';


function CodeView(props) {
    const [match] = useState(API.get_match());
    const [passes] = useState(API.passes);
    const [current_pass, setCurrentPass] = useState(API.passes[0]);

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
            <div style={{"height":"100%", "margin":0, "float":"left"}}>
                <Side height={props.top_height} files={match.files_a()}/>
            </div>
            <div style={{"height":"100%", "margin":0, "float":"left"}}>
                <Side height={props.top_height} files={match.files_b()}/>
            </div>
        </Split>
    )
}


function Side(props) {
    let [fileInView, setFileInView] = useState(props.files[0].name);

    // Keep track of the visilibity of each file in the viewport
    let fileVisibilities = useRef({
        "maxFile": props.files[0].name,
        "maxVisibility": 0,
        "visibilities": props.files.reduce((acc, curr) => {
            acc[curr.name] = 0;
            return acc;
        }, {})
    });

    // Callback for when the visibility of a file in the viewport changes
    const updateFileVisibility = (filename, visibility) => {
        fileVisibilities.current.visibilities[filename] = visibility;

        // Find the file with the most visibility in the viewport
        let maxFile = props.files[0].name;
        let maxVisibility = fileVisibilities.current.visibilities[maxFile];
        props.files.forEach(file => {
            let vis = fileVisibilities.current.visibilities[file.name]
            if (vis > maxVisibility) {
                maxVisibility = vis;
                maxFile = file.name;
            }
        });

        fileVisibilities.current.maxVisibility = maxVisibility;

        // If the file with the most visibility is different from the last, update fileInView
        if (fileVisibilities.current.maxFile !== maxFile) {
            fileVisibilities.current.maxFile = maxFile;
            setFileInView(maxFile);
        }
    }

    return (
        <div className="column-box">
            <div className="row auto" style={{
                "height":props.height,
                "lineHeight":props.height
            }}>
                <StatusBar
                    filepath="looooooooooooooooooooooooooooooooooooooooooooong/file/path/to/submission_a"
                    percentage={70}
                    file={fileInView}/>
            </div>
            <div className="row fill" style={{"overflow":"scroll"}}>
                <Code files={props.files} updateFileVisibility={updateFileVisibility}/>
            </div>
        </div>
    )
}


function StatusBar(props) {
    const filepathRef = useRef(null);

    useEffect(() => {
        // Horrible hack
        // As of writng, July 21 2020
        // Chrome does not scroll all the way left, unless it's delayed a little
        setTimeout(() => {
            const elem = filepathRef.current;
            elem.scrollLeft = elem.scrollWidth;
        }, 1);
    });

    return (
        <div className="row-box" style={{"font-weight":"bold"}}>
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


function Code(props) {
    console.log('RENDERING')
    return (
        <div style={{"paddingLeft":".5em"}}>
            {props.files.map(file => <File key={file.name} file={file} updateFileVisibility={props.updateFileVisibility}/>)}
        </div>
    )
}

// Only rerender code if its files change
Code = React.memo(Code, (prev, next) => prev.files == next.files);


function File(props) {
    const [ref, entry] = useIntersect({
        threshold: Array.from(Array(100).keys(), i => i / 100),
    });

    useEffect(() => {
        props.updateFileVisibility(props.file.name, entry.intersectionRatio);
    });

    return (
        <>
            <h4> {props.file.name} <span>({props.file.percentage}%)</span></h4>
            <pre ref={ref}>
                {props.file.content}
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


export default CodeView
