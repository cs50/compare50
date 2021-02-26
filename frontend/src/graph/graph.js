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
        this.d3Graph = null;
    }

    static defaultProps = {
        // mouseenter, mouseleave, select callbacks take in a node; the others take in nothing
        callbacks: {loaded: () => {}, mouseenter: (node) => {}, mouseleave: (node) => {}, select: (node) => {}, deselect: () => {}},
        color: null,
        slider: true,
        sliderTip: true
    }

    componentDidMount() {
        this.d3Graph = new D3Graph.D3Graph(this.graph.current, {
            radius: 10,
            width: this.props.width,
            height: this.props.height,
            color: this.props.color,
            callbacks: this.props.callbacks,
        });

        if (this.props.slider) {
            this.d3Graph.addSlider(this.slider.current);
        }

        // Initialize the graph
        this.d3Graph.load(this.props.graph);
    }

    componentDidUpdate() {
        // Resize the graph
        this.d3Graph.on_resize();

        // Update the graph
        this.d3Graph.update();

        this.d3Graph.setHighlight(this.props.highlight);
    }

    componentWillUnmount() {
        this.d3Graph.destroy();
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