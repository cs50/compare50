import React from 'react';

import './sidebar.css';


function SideBar(props) {
    let style = {
        "margin": "auto",
        "marginBottom": "1em",
        "marginTop": "1em",
        "width": "90%"
    }

    const updateGlobalState = newState => props.setGlobalState({...props.globalState, ...newState})


    return (
        <div style={{
            "height":"100%"
        }}>
            <div style={{...style, ...{"marginTop": "0"}}}>
                <MatchNavigation
                    current={props.globalState.currentMatch}
                    n={props.globalState.nMatches}
                    setMatch={match => updateGlobalState({"currentMatch": match})}
                />
            </div>
            <div style={style}>
                <PassNavigation
                    passes={props.globalState.passes}
                    setPass={pass => updateGlobalState({"currentPass": pass})}
                />
            </div>
            <div style={style}>
                <GroupNavigation
                    current={props.globalState.currentGroup}
                    n={props.globalState.nGroups}
                    setGroup={group => updateGlobalState({"currentGroup": group})}
                />
            </div>
            <div style={style}>
                <ConfigMenu
                    softWrap={props.globalState.softWrap}
                    setSoftWrap={softWrap => updateGlobalState({"softWrap": softWrap})}
                />
            </div>
            <div style={style}>
                <ExportMenu/>
            </div>
        </div>
    )
}


function MatchNavigation(props) {
    return (
        <div>
            <div style={{
                "textAlign": "center",
                "paddingBottom": ".1em",
                "paddingTop": ".5em",
                "color": "black"
            }}>
                {props.current} / {props.n}
            </div>
            <div className="btn-group horizontal">
                <button type="button" style={{"width":"50%"}}>{"<<"}</button>
                <button type="button" style={{"width":"50%"}}>{">>"}</button>
            </div>
        </div>
    )
}


function PassNavigation(props) {
    return (
        <div className="btn-group vertical">
            {props.passes.map(pass =>
                <button key={`pass_${pass.name}`} type="button" title={pass.docs} style={{"width":"100%"}}>
                    {pass.name}
                </button>
            )}
        </div>
    )
}


function GroupNavigation(props) {
    return (
        <div>
            <div style={{
                "textAlign": "center",
                "paddingBottom": ".1em",
                "color": "black"
            }}>
                {props.current} / {props.n}
            </div>
            <div className="btn-group horizontal" style={{"width":"100%"}}>
                <button type="button" style={{"width":"50%"}}>&lt;</button>
                <button type="button" style={{"width":"50%"}}>&gt;</button>
            </div>
        </div>
    )
}


function ExportMenu(props) {
    return (
        <div className="btn-group vertical">
            <button type="button" style={{"width":"100%"}}>PDF</button>
        </div>
    )
}


function ConfigMenu(props) {
    return (
        <Switch text="wrap" default={props.softWrap} setOption={props.setSoftWrap}/>
    )
}


function Switch(props) {
    // https://stackoverflow.com/questions/2939914/how-do-i-vertically-align-text-in-a-div
    return (
        <div style={{"display": "table", "margin": "auto"}}>
            <label className="switch" style={{"float":"left"}}>
                <input type="checkbox" onChange={event => props.setOption(event.target.checked)} defaultChecked={props.default}/>
                <span className="slider round"></span>
            </label>
            <div style={{"display": "table-cell", "verticalAlign": "middle", "paddingLeft": ".5em"}}>
                {props.text}
            </div>
        </div>
    )
}


export default SideBar;
