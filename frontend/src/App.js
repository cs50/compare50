import React from 'react';
import './App.css';
import Split from 'react-split';


class App extends React.Component {
    render() {
        return (
            <div>
                <TopBar />
                <SideBar />
                <CodeView />
            </div>
        );
    }
}

class TopBar extends React.Component {
    render() {
        return (
            <div style={{"height":"100px", "width":"100%", "float":"left", "background-color": "orange"}}>navigation</div>
        )
    }
}

class SideBar extends React.Component {
    render() {
        return (
            <div style={{"height":"500px", "width": "10%", "margin":0, "float":"left", "background-color": "green"}}>foo</div>
        )
    }
}

class CodeView extends React.Component {
    render() {
        return (
            <Split
                sizes={[45, 45]}
                gutterSize={10}
                gutterAlign="center"
                snapOffset={30}
                dragInterval={1}
                direction="horizontal"
                cursor="col-resize"
            >
                <div style={{"height":"500px", "margin":0, "float":"left", "background-color": "#D3D3D3"}}>code</div>
                <div style={{"height":"500px", "margin":0, "float":"left", "background-color": "#D3D3D3"}}>code</div>
            </Split>
        )
    }
}

export default App;
