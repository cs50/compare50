import React from 'react';
import '../index.css';
import './graph.css';

import d3Graph from './graph-d3';

class Graph extends React.PureComponent {
    constructor(props) {
        super(props);
        this.graph = React.createRef();
        this.slider = React.createRef();
    }

    componentDidMount() {
        // Initialize the graph
        d3Graph.create(
            this.graph.current,
            this.slider.current,
            this.getProps(),
            this.getChartState());
    }

    componentDidUpdate() {
        // Update the graph
        d3Graph.update(
            this.graph.current,
            this.getProps(),
            this.getChartState());
    }

    getChartState() {
        // Assumes the graph is passed in JSON format as a prop
        return {
            graph: JSON.parse(this.props.graph)
        };
    }

    getProps() {
        // Important information about displaying the graph
        return {
            radius: 10,
            width: this.props.width,
            height: this.props.height
        }
    }

    componentWillUnmount() {
        d3Graph.destroy(this.graph.current);
    }
  
    render() {
        return (
            <>
                <svg className="d3graph" ref={this.graph}></svg>
                <div className="d3slider" ref={this.slider}></div>
            </>
        )
    }
};

export default Graph;