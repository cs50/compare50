import React from 'react';
import Split from 'react-split';

import API from './api';

import './App.css';
import './split.css';


class CodeView extends React.Component {
    constructor(props) {
        super(props);

        this.state = {
            "match": API.get_match(),
            "passes": API.passes,
            "current_pass": API.passes[0]
        }
    }

    render() {
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
                    <Side height={this.props.top_height} code={this.state.match.code_a()}/>
                </div>
                <div style={{"height":"100%", "margin":0, "float":"left"}}>
                    <Side height={this.props.top_height} code={this.state.match.code_b()}/>
                </div>
            </Split>
        )
    }
}


class Side extends React.Component {
    // constructor(props) {
    //     super(props);
    //
    //     this.state = {
    //         "code": props.code
    //     }
    // }

    render() {
        return (
            <div className="column-box">
                <div className="row auto" style={{
                    "height":this.props.height,
                    "lineHeight":this.props.height
                }}>
                    <TopBar filepath="looooooooooooooooooooooooooooooooooooooooooooong/file/path/to/submission_a"
                                   percentage={70}
                                   file_in_view="foo.c"/>
                </div>
                <div className="row fill" style={{"overflow":"scroll"}}>
                    <Code code={this.props.code}/>
                </div>
            </div>
        )
    }
}


class TopBar extends React.Component {
    constructor(props) {
        super(props);
        this.state = {
            "file_in_view": props.file_in_view
        };
        this.filepath_ref = React.createRef();
    }

    update_file(file_in_view) {
        this.setState({
            "file_in_view": file_in_view
        })
    }

    render() {
        return (
            <div className="row-box" style={{"font-weight":"bold"}}>
                <div ref={this.filepath_ref} className="row fill" style={{
                    "overflow":"scroll",
                    "marginLeft":"5px",
                    "marginRight":"5px"
                }}>
                    {this.props.filepath}
                </div>
                <div className="row auto" style={{
                    "width":"4em",
                    "textAlign":"center"
                }}>
                    {`${this.props.percentage}%`}
                </div>
                <div className="row auto" style={{
                    "width":"10em",
                    "textAlign":"center"
                }}>
                    {this.state.file_in_view}
                </div>
            </div>
        )
    }

    componentDidMount() {
        // Scroll the filepath all the way to the right
        let filepath_elem = this.filepath_ref.current;

        // Horrible hack
        // As of writng, July 21 2020
        // Chrome does not scroll all the way left, unless it's delayed a little
        setTimeout(() => {
            filepath_elem.scrollLeft = filepath_elem.scrollWidth;
        }, 1);

    }
}


class Code extends React.Component {
    render() {
        return (
            <div style={{"paddingLeft":".5em"}}>
                <pre>
                    {this.props.code}
                </pre>
            </div>
        )
    }
}


export default CodeView
