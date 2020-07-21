import React from 'react';

class TopBar extends React.Component {
    constructor(props) {
        super(props);
        this.height = props.height || "3em";
    }

    render() {
        return (
            <div style={{"width": "100%"}}>
                <Logo height={this.height} width="10%"/>
                <div style={{
                    "height":this.height,
                    "line-height":this.height,
                    "width":"90%",
                    "float":"left",
                    "background-color": "orange"
                }}>
                    <SubmissionBar height={this.height}
                                   width="50%"
                                   filepath="looooooooooooooooooooooooooooooooooooooooooooong/file/path/to/submission_a"
                                   percentage={70}
                                   file_in_view="foo.c"/>
                    <SubmissionBar height={this.height}
                                   width="50%"
                                   filepath="long/file/path/to/submission_b"
                                   percentage={60}
                                   file_in_view="bar.c"/>
                </div>
            </div>
        )
    }
}


function Logo(props) {
    return (
        <div style={{
            "width":props.width,
            "height":props.height,
            "line-height":props.height,
            "text-align":"center",
            "float":"left"
        }}>compare50</div>
    )
}

class SubmissionBar extends React.Component {
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
            <div style={{
                "width":this.props.width,
                "height":this.props.height,
                "line-height":this.props.height,
                "float":"left"
            }}>
                <div ref={this.filepath_ref} style={{
                    "width":"70%",
                    "float":"left",
                    "padding-left":"10px",
                    "white-space": "nowrap",
                    "overflow-x": "scroll"
                }}>
                    {this.props.filepath}
                </div>
                <div style={{
                    "width":"20%",
                    "float":"left",
                    "text-align":"center",
                    "padding-left":"10px"
                }}>
                    {this.state.file_in_view}
                </div>
                <div style ={{
                    "width": "10%",
                    "float":"left",
                    "text-align":"center",
                    "padding-left":"10px"
                }}>
                    {`${this.props.percentage}%`}
                </div>
            </div>
        )
    }

    componentDidMount() {
        // Scroll the filepath all the way to the right
        let filepath_elem = this.filepath_ref.current
        filepath_elem.scrollLeft = filepath_elem.scrollWidth;
    }
}


export default TopBar;
