import React from 'react';
import ReactDOM from 'react-dom';
import '../index.css';



class Graph extends React.Component {

    constructor(props) {
      super(props);
      this.state = {d3: ''}
    }
  
    componentDidMount() {
      this.setState({d3: init_graph()});
    }
  
    render() {
      return (
        <div>
          <RD3Component data={this.state.d3} />
        </div>
      )
    }
  };

export default Graph;