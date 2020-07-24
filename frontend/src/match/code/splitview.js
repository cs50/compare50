import React, {useState, useRef, useEffect} from 'react';
import Split from 'react-split';

import API from '../../api';
import createFragments from './fragmentslicer'
import File from './file'

import '../app.css';
import './split.css';


function SplitView(props) {
    const [match] = useState(API.get_match());
    const [passes] = useState(API.passes);
    const [current_pass, setCurrentPass] = useState(API.passes[0]);

    const pass = match.get_pass(current_pass);

    const attachFragments = file => {
        file.fragments = createFragments(file, pass);
        return file;
    };

    const filesA = match.files_a().map(attachFragments);
    const filesB = match.files_b().map(attachFragments);

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
                <Side height={props.top_height} files={filesA}/>
            </div>
            <div style={{"height":"100%", "margin":0, "float":"left"}}>
                <Side height={props.top_height} files={filesB}/>
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
                <div style={{"paddingLeft":".5em"}}>
                    {props.files.map(file => <File key={file.name} file={file} updateFileVisibility={updateFileVisibility}/>)}
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
        <div className="row-box" style={{"fontWeight":"bold"}}>
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


export default SplitView
