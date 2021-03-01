import React from 'react';
import Split from 'react-split';
import ReactTooltip from "react-tooltip";

import '../index.css';
import '../split.css';
import API from '../api';
import Graph from '../graph/graph';
import MatchTable from './matchtable';
import Logo from '../logo';

class HomeView extends React.Component {
    constructor(props) {
        super(props);
        this.state = {
            graph: null,
            highlighted: null,
            selected: null,
            forceUpdateGraph: false,
            forceUpdateTable: true,
            isDataLoaded: false
        };
    }

    drag = () => {
        this.setState({forceUpdateGraph: !this.state.forceUpdateGraph});
    }

    graphCallbacks = {
        loaded: () => {
            this.setState({forceUpdateTable: !this.state.forceUpdateTable});
        },

        mouseenter: (event) => {
            const nodeId = event.id;
            const group = event.group;
            this.setState({highlighted: {
                "group": group,
                "nodes": [nodeId]
            }});
        },

        mouseleave: () => {
            this.setState({highlighted: null});
        },

        select: (event) => {
            const nodeId = event.id;
            const group = event.group;
            this.setState({selected: {
                "id": nodeId,
                "group": group
            }});
        },

        deselect: () => {
            this.setState({selected: null});
        }
    }

    tableCallbacks = {
        mouseenter: (event) => {
            this.setState({highlighted: {
                group: event.group,
                nodes: [event.submissionA, event.submissionB]
            }});
        },

        mouseleave: () => {
            this.setState({highlighted: null});
        }
    }

    componentDidMount() {
        API.getGraph().then(graph => {
            this.setState({
                graph: graph,
                isDataLoaded: true
            });
        });
    }

    render() {
        if (!this.state.isDataLoaded) {
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
                    <div style={{
                        "margin-top": "20px"
                    }}>
                        <Logo />
                    </div>
                    <MatchTable
                        forceUpdate={this.forceUpdateTable}
                        callbacks={this.tableCallbacks}
                        graph={this.state.graph}
                        highlighted={this.state.highlighted}
                        selected={this.state.selected} />
                </div>
                <div style={{"height":"100%", "margin":0, "float":"left", "background": "#ffffff"}}>
                    <Graph
                        forceUpdate={this.state.forceUpdateGraph}
                        callbacks={this.graphCallbacks}
                        graph={this.state.graph}
                        highlighted={this.state.highlighted}
                        slider={true}
                        sliderTip={true} />
                </div>
            </Split>
        </>
        );
    }
}

export default HomeView;
