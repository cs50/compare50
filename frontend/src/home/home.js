
import React from 'react';
import Split from 'react-split';

import '../index.css';
import '../split.css';
import Logo from '../match/logo';
import Graph from './graph';
import GraphFxns from './graph-d3';

var d3 = require("d3");

class MatchTableRow extends React.Component {
    constructor(props) {
        super(props);
    }

    goTo = () => {
        window.location = "/match_" + this.props.link.index + ".html";
    }

    render() {
        let style = {
            borderRightColor: this.props.color,
            borderRightWidth: "10px",
            borderRightStyle: "solid"};

        return (
        <tr
            key={this.props.link.index}
            onClick={this.goTo}
            >
            <td>{this.props.link.index + 1}</td>
            <td>{this.props.link.source}</td>
            <td>{this.props.link.target}</td>
            <td style={style}>{Math.round(this.props.link.value * 10) / 10}</td>
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
        let node_groups = {};
        data.nodes.forEach(n => {node_groups[n.id] = n.group});
        let rows = data.links.map(link => <MatchTableRow link={link} key={link.index} color={this.props.color(node_groups[link.source])} />)

        return (
            <table>
                <thead>
                    <tr>
                        <th>#</th>
                        <th colSpan="2">Submissions</th>
                        <th colSpan="2">Score</th>
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
        this.state = {color: null, graph: JSON.parse(this.props.data), graphJSON: this.props.data, update_graph: 0};

        // assign groups to nodes
        let group_map = GraphFxns.get_group_map(this.state.graph.links);
        this.state.graph.nodes.forEach(d => d.group = group_map[d.id]);

        // set COLOR (function from group => color)
        let n_groups = Math.max.apply(0, this.state.graph.nodes.map(node => node.group));
        this.state.color = d3.scaleSequential().domain([0, n_groups + 1]).interpolator(d3.interpolateRainbow);
        this.state.graphJSON = JSON.stringify(this.state.graph)
    }

    drag = () => {
        this.setState({update_graph: this.state.update_graph + 1});
    }

    componentDidMount() {

    }

    render() { 
        return (
        <>
            <Split
                sizes={[60, 40]}
                gutterSize={10}
                gutterAlign="center"
                snapOffset={30}
                dragInterval={1}
                direction="horizontal"
                cursor="col-resize"
                style={{
                    "height":"100%"
                }}
                onDrag={this.drag}
            >
                <div style={{"height":"100%", "margin":0, "float":"left", "overflow": "auto"}}>
                    <nav>
                        <Logo />
                    </nav>
                    <MatchTable
                        color={this.state.color}
                        data={this.state.graphJSON} />
                </div>
                <div style={{"height":"100%", "margin":0, "float":"left", "background": "#ffffff"}}>
                    <Graph
                        forceUpdate={this.state.update_graph}
                        color={this.state.color}
                        graph={this.props.data} />
                </div>
            </Split>
        </>
        );
    }
}

export default HomeView;
