import React from 'react';

import './App.css';
import SideBar from './sidebar';
import Logo from './logo';
import CodeView from './codeview';


class App extends React.Component {
    render() {
        return (
            <div className="row-box" style={{"height":"100vh"}}>
              <div className="row auto" style={{"width":"10%"}}>
                  <div className="column-box" >
                      <div className="row auto">
                          <Logo height="2.5em"/>
                      </div>
                      <div className="row fill">
                          <SideBar/>
                      </div>
                  </div>
              </div>
              <div className="row fill">
                  <div className="column-box">
                      <div className="row fill">
                          <CodeView top_height="2.5em"/>
                      </div>
                  </div>
              </div>
            </div>
        );
    }
}

export default App;
