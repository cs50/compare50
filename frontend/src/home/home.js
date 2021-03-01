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
            highlight: null,
            tableHighlighted: null,
            tableSelected: null,
            updateGraph: false,
            updateTable: true,
            isDataLoaded: false
        };
    }

    drag = () => {
        this.setState({updateGraph: !this.state.updateGraph});
    }

    graphCallbacks = {
        loaded: (evt) => {
            this.setState({updateTable: !this.state.updateTable});
        },

        mouseenter: (d) => {
            if (this.state.tableHighlighted === null || !this.state.tableHighlighted.clicked) {
                this.setState({tableHighlighted: d});
            }
        },

        mouseleave: (d) => {
            this.setState({tableHighlighted: null});
        },

        select: (d) => {
            this.setState({tableSelected: d});
        },

        deselect: (d) => {
            this.setState({tableSelected: null});
        }
    }

    tableCallbacks = {
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
                        forceUpdate={this.updateTable}
                        callbacks={this.tableCallbacks}
                        graph={this.state.graph}
                        highlight={this.state.tableHighlighted}
                        selected={this.state.tableSelected} />
                </div>
                <div style={{"height":"100%", "margin":0, "float":"left", "background": "#ffffff"}}>
                    <Graph
                        callbacks={this.graphCallbacks}
                        highlight={this.state.highlight}
                        forceUpdate={this.state.updateGraph}
                        graph={this.state.graph}
                        sliderTip={true} />
                </div>
            </Split>
        </>
        );
    }
}

export default HomeView;
