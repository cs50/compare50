import React from 'react';


class SideBar extends React.Component {
    render() {
        let style = {
            "margin": "auto",
            "marginBottom": "1em",
            "marginTop": "1em",
            "width": "90%"
        }

        return (
            <div style={{
                "backgroundColor":"green",
                "height":"100%"
            }}>
                <div style={{...style, ...{"marginTop": "0"}}}>
                    <MatchNavigation current={1} n={50}/>
                </div>
                <div style={style}>
                    <PassNavigation passes={[
                        {name:"structure", docs:"foo"},
                        {name:"exact", docs:"bar"},
                        {name:"misspellings", docs:"baz"},
                    ]}/>
                </div>
                <div style={style}>
                    <ExportMenu/>
                </div>
                <div style={style}>
                    <GroupNavigation current={1} n={6}/>
                </div>
            </div>
        )
    }
}


class MatchNavigation extends React.Component {
    constructor(props) {
        super(props);
        this.state = {
            "current": props.current,
            "n": props.n
        }
    }

    render() {
        return (
            <div>
                <div style={{
                    "textAlign": "center",
                    "paddingBottom": ".1em",
                    "paddingTop": ".5em",
                    "color": "white"
                }}>
                    {this.state.current} / {this.state.n}
                </div>
                <div className="btn-group horizontal">
                    <button type="button" style={{"width":"50%"}}>{"<<"}</button>
                    <button type="button" style={{"width":"50%"}}>{">>"}</button>
                </div>
            </div>
        )
    }
}

class PassNavigation extends React.Component {
    constructor(props) {
        super(props);
        this.state = {
            "passes": props.passes
        }
    }

    render() {
        return (
            <div className="btn-group vertical">
                {this.state.passes.map(pass =>
                    <button type="button" title={pass.docs} style={{"width":"100%"}}>
                        {pass.name}
                    </button>
                )}
            </div>
        )
    }
}


class GroupNavigation extends React.Component {
    constructor(props) {
        super(props);
        this.state = {
            "current": props.current,
            "n": props.n
        }
    }

    render() {
        return (
            <div>
                <div style={{
                    "textAlign": "center",
                    "paddingBottom": ".1em",
                    "color": "white"
                }}>
                    {this.state.current} / {this.state.n}
                </div>
                <div className="btn-group horizontal" style={{"width":"100%"}}>
                    <button type="button" style={{"width":"50%"}}>&lt;</button>
                    <button type="button" style={{"width":"50%"}}>&gt;</button>
                </div>
            </div>
        )
    }
}


class ExportMenu extends React.Component {
    render() {
        return (
            <div className="btn-group vertical">
                <button type="button" style={{"width":"100%"}}>PDF</button>
            </div>
        )
    }
}



export default SideBar;
