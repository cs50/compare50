import React from 'react';
import '../index.css';
import './graph.css';

import D3Graph from './graph-d3';

class Graph extends React.Component {
    constructor(props) {
        super(props);
        this.divRef = React.createRef();
        this.graphRef = React.createRef();
        this.sliderRef = React.createRef();
        this.d3Graph = null;
    }

    componentDidMount() {
        this.d3Graph = new D3Graph.D3Graph(this.graphRef.current, {
            radius: 10,
            width: this.props.width,
            height: this.props.height,
            color: this.props.color,
            callbacks: this.props.callbacks,
        });

        if (this.props.slider) {
            this.d3Graph.addSlider(this.sliderRef.current);
        }

        // Initialize the graph
        this.d3Graph.load(this.props.graph);

        window.addEventListener("resize", this.d3Graph.onResize.bind(this.d3Graph));
    }

    componentDidUpdate() {
        this.d3Graph.setHighlighted(this.props.highlighted);
    }

    componentWillUnmount() {
        window.removeEventListener("resize", this.d3Graph.onResize.bind(this.d3Graph));
        this.d3Graph.destroy();
    }

    render() {
        return (
            <div ref={this.divRef} style={{"width": "100%", "height":"100%"}}>
                <svg className="d3graph" ref={this.graphRef}></svg>
                <div className="d3slider" ref={this.sliderRef}>
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
