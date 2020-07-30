import React from 'react';
import Split from 'react-split';

import '../index.css';
import '../split.css';
import Logo from '../match/logo';
import Graph from './graph'

class MatchTableRow extends React.Component {
    constructor(props) {
        super(props);
    }

    goTo = () => {
        window.location = "/match_" + this.props.link.index;
    }

    render() {
        return (
        <tr key={this.props.link.index} onClick={this.goTo}>
            <td>{this.props.link.index + 1}</td>
            <td>{this.props.link.source}</td>
            <td>{this.props.link.target}</td>
            <td>{this.props.link.value}</td>
        </tr>
        );
    }
}

class MatchTable extends React.Component {
    constructor(props) {
        super(props);
    }

    render() {
        let data = JSON.parse(this.props.data);
        let rows = data.links.map(link => <MatchTableRow link={link} />)

        return (
            <table>
                <thead>
                    <tr>
                        <th>#</th>
                        <th colSpan="2">Submissions</th>
                        <th>Score</th>
                    </tr>
                </thead>
                <tbody>
                    {rows}
                </tbody>
            </table>
        );
    }
}

class HomeView extends React.Component {
    constructor(props) {
        super(props);
        this.state = {graph_width: undefined}
    }

    // This makes sure the graph actually rescales as needed
    updateGraphWidth = (sizes) => {
        this.setState({graph_width: undefined});
    }

    componentDidMount() {
        setTimeout(() => {
            this.updateGraphWidth();
        }, 66);
    }

    render() { 
        return (
        <>
            <Logo />
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
                onDrag={this.updateGraphWidth}
            >
                <div style={{"height":"100%", "margin":0, "float":"left"}}>
                    <MatchTable data={this.props.data} />
                </div>
                <div style={{"height":"100%", "margin":0, "float":"left", "background": "#ffffff"}}>
                    <Graph
                        graph={this.props.data}
                        width={this.state.graph_width}
                        height="300" />
                </div>
            </Split>
        </>
        );
    }
}

export default HomeView;
