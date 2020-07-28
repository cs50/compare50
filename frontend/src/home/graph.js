import React from 'react';
import ReactDOM from 'react-dom';
import '../index.css';

import d3Graph from './g';

// var GRAPH = {"data": {"../check50-ja/check50": {"is_archive": false}, "../check50/check50": {"is_archive": false}}, "links": [{"index": 0, "source": "../check50/check50", "target": "../check50-ja/check50", "value": 10.0}], "nodes": [{"id": "../check50-ja/check50"}, {"id": "../check50/check50"}]};


class Graph extends React.PureComponent {

    constructor(props) {
      super(props);
      this.graph = React.createRef();
    }

    componentDidMount() {
      d3Graph.create(this.graph.current, {
        radius: 10,
        width: 400,
        height: 300
      }, this.getChartState());
    }

    componentDidUpdate() {
      d3Graph.update(this.graph.current, {radius: 10, width: "100%", height: "300px"}, this.getChartState());
    }

    getChartState() {
      return {
        graph: JSON.parse(this.props.graph)
      };
    }

    componentWillUnmount() {
      //d3Graph.destroy(el);
    }
  
    render() {
      return (
        <svg className="d3graph" ref={this.graph} width="100%" height="300px"></svg>
      )
    }
};

export default Graph;