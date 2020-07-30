import React from 'react';
import '../index.css';
import './graph.css';

import D3Graph from './graph-d3';

class Graph extends React.PureComponent {
    constructor(props) {
        super(props);
        this.graph = React.createRef();
        this.slider = React.createRef();
        this.divRef = React.createRef();
        this.d3Graph = new D3Graph();
    }

    componentDidMount() {
        // Initialize the graph
        this.d3Graph.create(
            this.graph.current,
            this.slider.current,
            this.getProps(),
            this.getGraphState());
    }

    componentDidUpdate() {
        // Update the graph
        this.d3Graph.update(
            this.graph.current,
            this.getProps(),
            this.getGraphState());
    }

    getGraphState() {
        return {
            graph: this.props.graph
        };
    }

    getProps() {
        // TODO looks like 120 is the slider height, but the height of this component should probably include the slider

        const minWidth = 100;
        const minHeight = 200;

        // Important information about displaying the graph
        return {
            radius: 10,
            width: Math.max(this.props.width || this.divRef.current.offsetWidth, minWidth),
            height: Math.max(this.props.height || this.divRef.current.offsetHeight - 120, minHeight)
        }
    }

    componentWillUnmount() {
        this.d3Graph.destroy(this.graph.current);
    }

    render() {
        return (
            <div ref={this.divRef} style={{"width": "100%", "height":"100%"}}>
                <svg className="d3graph" ref={this.graph}></svg>
                <div className="d3slider" ref={this.slider}></div>
            </div>
        )
    }
};

export default Graph;
