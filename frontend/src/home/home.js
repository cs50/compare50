
import React from 'react';
import Split from 'react-split';
import ReactTooltip from "react-tooltip";

import '../index.css';
import '../split.css';
import API from '../api';
import Logo from '../logo';
import Graph from '../graph/graph';
import GraphFxns from '../graph/graph-d3';

var d3 = require("d3");

class MatchTableRow extends React.Component {
    constructor(props) {
        super(props);
    }

    callbacks = {
        mouseenter: () => {
            this.props.callbacks.mouseenter({link: this.props.link, group: this.props.nodeGroup});
        }
    }

    goTo = () => {
        window.location = "/match_" + this.props.link.index + ".html";
    }

    render() {
        let last_td_style = {
            borderRightColor: this.props.color,
            borderRightWidth: "10px",
            borderRightStyle: "solid"
        };

        let tr_style = {}, source_style = {}, target_style = {};
        if (this.props.highlight !== null) {
            let hl = this.props.highlight;
            tr_style.backgroundColor = this.props.selected === null && !hl.clicked && hl.group === this.props.nodeGroup ? "#ececec" : undefined;
            source_style.backgroundColor = !hl.clicked && hl.id === this.props.link.source.id ? "#ccc" : undefined;
            target_style.backgroundColor = !hl.clicked && hl.id === this.props.link.target.id ? "#ccc" : undefined;
        }

        if (this.props.selected !== null) {
            let sl = this.props.selected;
            source_style.fontWeight = sl.id === this.props.link.source.id ? "bold" : undefined;
            target_style.fontWeight = sl.id === this.props.link.target.id ? "bold" : undefined;
        }

        return (
        <tr
            style={tr_style}
            key={this.props.link.index}
            onClick={this.goTo}
            onMouseEnter={this.callbacks.mouseenter}
            onMouseLeave={this.props.callbacks.mouseleave}
        >
            <td>{this.props.link.index + 1}</td>
            <td style={source_style} data-tip={this.props.link.source.id}>{this.props.link.source.id}</td>
            <td style={target_style} data-tip={this.props.link.target.id}>{this.props.link.target.id}</td>
            <td style={last_td_style}>{Math.round(this.props.link.value * 10) / 10}</td>
        </tr>
        );
    }
}

class MatchTable extends React.Component {
    constructor(props) {
        super(props);
    }

    callbacks = {
        mouseenter: (evt) => {
            this.props.callbacks.mouseenter(evt)
        },
        mouseleave: this.props.callbacks.mouseleave
    }

    render() {
        let data = this.props.data;
        let node_groups = {};
        data.nodes.forEach(n => {node_groups[n.id] = n.group});
        let rows = data.links.map(link => <MatchTableRow link={link} key={link.index} color={this.props.color(node_groups[link.source.id])} callbacks={this.callbacks} nodeGroup={node_groups[link.source.id]} highlight={this.props.highlight} selected={this.props.selected} />)

        return (
            <table>
                <thead>
                    <tr>
                        <th>#</th>
                        <th colSpan="2">Submissions</th>
                        <th colSpan="2">Score <span data-tip="On a scale of 1-10, how similar the files are." className="tooltip-marker">?</span></th>
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
        this.state = {
            color: null,
            graph: null,
            highlight: null,
            table_highlighted: null,
            table_selected: null,
            update_graph: false,
            update_table: true,
            is_data_loaded: false
        };
    }

    drag = () => {
        this.setState({update_graph: !this.state.update_graph});
    }

    graph_callbacks = {
        loaded: (evt) => {
            this.setState({update_table: !this.state.update_table});
        },

        mouseenter: (d) => {
            if (this.state.table_highlighted === null || !this.state.table_highlighted.clicked) {
                this.setState({table_highlighted: d});
            }
        },

        mouseleave: (d) => {
            this.setState({table_highlighted: null});
        },

        select: (d) => {
            this.setState({table_selected: d});
        },

        deselect: (d) => {
            this.setState({table_selected: null});
        }
    }

    table_callbacks = {
        mouseenter: (event) => {
            let highlight = {
                group: event.group,
                nodes: [event.link.source, event.link.target]
            };
            this.setState({highlight: highlight});
        },

        mouseleave: (event) => {
            this.setState({highlight: null});
        }
    }

    componentDidMount() {
        API.getGraph().then(graph => {
            // assign groups to nodes
            const group_map = GraphFxns.get_group_map(graph.links);
            graph.nodes.forEach(d => d.group = group_map[d.id]);

            // set COLOR (function from group => color)
            const n_groups = Math.max.apply(0, graph.nodes.map(node => node.group));
            const color = d3.scaleSequential().domain([0, n_groups + 1]).interpolator(d3.interpolateRainbow);

            this.setState({
                graph: graph,
                color: color,
                is_data_loaded: true
            });
        });
    }

    render() {
        if (!this.state.is_data_loaded) {
            return (
                <div></div>
            );
        }

        let sizes = this.state.graph.nodes.length > 50 ? [55, 45] : [60, 40];

        return (
        <>
            <ReactTooltip />
            <Split
                sizes={sizes}
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
                        forceUpdate={this.update_table}
                        callbacks={this.table_callbacks}
                        color={this.state.color}
                        data={this.state.graph}
                        highlight={this.state.table_highlighted}
                        selected={this.state.table_selected} />
                </div>
                <div style={{"height":"100%", "margin":0, "float":"left", "background": "#ffffff"}}>
                    <Graph
                        callbacks={this.graph_callbacks}
                        highlight={this.state.highlight}
                        forceUpdate={this.state.update_graph}
                        color={this.state.color}
                        graph={this.state.graph}
                        sliderTip={true} />
                </div>
            </Split>
        </>
        );
    }
}

export default HomeView;
