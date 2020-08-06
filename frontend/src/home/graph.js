import React from 'react';
import '../index.css';
import './graph.css';

import D3Graph from './graph-d3';

class Graph extends React.Component {
    constructor(props) {
        super(props);
        this.divRef = React.createRef();
        this.graph = React.createRef();
        this.slider = React.createRef();
        this.d3Graph = new D3Graph.D3Graph();
    }

    static defaultProps = {
        // mouseenter, mouseleave, select callbacks take in a node; the others take in nothing
        callbacks: {loaded: () => {}, mouseenter: (node) => {}, mouseleave: (node) => {}, select: (node) => {}, deselect: () => {}},
        color: null,
        slider: true,
        sliderTip: true
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
            graph: this.props.graph,
            highlight: this.props.highlight
        };
    }

    getProps() {
        // TODO looks like 120 is the slider height, but the height of this component should probably include the slider

        const minWidth = 100;
        const minHeight = 200;

        // Important information about displaying the graph
        return {
            radius: 10,
            width: this.props.width,
            height: this.props.height,
            slider: this.props.slider,
            color: this.props.color,
            callbacks: this.props.callbacks,
            sliderTip: this.props.sliderTip
        }
    }

    componentWillUnmount() {
        this.d3Graph.destroy(this.graph.current);
    }

    render() {
        return (
            <div ref={this.divRef} style={{"width": "100%", "height":"100%"}}>
                <svg className="d3graph" ref={this.graph}></svg>
                <div className="d3slider" ref={this.slider}>
                    {this.props.sliderTip &&
                    <small
                        className="tooltip-marker"
                        style={{position: "absolute", marginTop: "20px"}}
                        data-tip="Slide this to hide all matches below the selected score."
                    >
                        ?
                    </small>
                    }
                </div>
            </div>
        )
    }
};

export default Graph;
