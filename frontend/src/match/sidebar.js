import React, {useRef, useEffect} from 'react';

import './matchview.css'
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
                    spanManager={props.spanManager}
                    setGroup={group => updateGlobalState({"currentGroup": group})}
                />
            </div>
            <div style={style}>
                <ConfigMenu
                    softWrap={props.globalState.softWrap}
                    setSoftWrap={softWrap => updateGlobalState({"softWrap": softWrap})}
                    hideIgnored={props.globalState.hideIgnored}
                    setHideIgnored={hideIgnored => updateGlobalState({"hideIgnored": hideIgnored})}
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
            <div className="monospace-text" style={{
                "textAlign": "center",
                "paddingBottom": ".1em",
                "paddingTop": ".5em",
                "color": "black"
            }}>
                {formatFraction(props.current, props.n)}
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
    const prevRef = useRef(null);
    const nextRef = useRef(null);

    useEffect(() => {
        const eventListener = (event) =>  {
            if (event.key === "]") {
                event.preventDefault();
                nextRef.current.click();
            }
            else if (event.key === "[") {
                event.preventDefault();
                prevRef.current.click();
            }
        };

        document.addEventListener("keyup", eventListener);

        return () => document.removeEventListener("keyup", eventListener);
    }, []);

    return (
        <div>
            <div className="monospace-text" style={{
                "textAlign": "center",
                "paddingBottom": ".1em",
                "color": "black"
            }}>
                {formatFraction(props.spanManager.selectedGroupIndex(), props.spanManager.nGroups())}
            </div>
            <div className="tooltip btn-group horizontal" style={{"width":"100%"}}>
                <button
                    ref={prevRef}
                    type="button"
                    style={{"width":"50%"}}
                    onClick={() => props.spanManager.selectPreviousGroup()}
                >
                    &lt;
                </button>
                <button
                    ref={nextRef}
                    type="button"
                    style={{"width":"50%"}}
                    onClick={() => props.spanManager.selectNextGroup()}
                >
                    &gt;
                </button>
                <span class="monospace-text tooltiptext bottom" style={{"fontSize":".65em"}}>{"Press '[' ']'"}</span>
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
        <React.Fragment>
            <div style={{"marginBottom": ".25em"}}>
                <Switch text="wrap" default={props.softWrap} setOption={props.setSoftWrap} tooltip="Soft Wrap long lines of code"/>
            </div>
            <div>
                <Switch text="hide" default={props.hideIgnored} setOption={props.setHideIgnored} tooltip="Hide code that was not used in the comparison"/>
            </div>
        </React.Fragment>
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
            <div className="tooltip" style={{"display": "table-cell", "verticalAlign": "middle", "paddingLeft": ".5em"}}>
                <span className="monospace-text">{props.text}</span>
                <span class="tooltiptext">{props.tooltip}</span>
            </div>
        </div>
    )
}


function formatFraction(numerator, denominator) {
    let nDigits = Math.max(numerator.toString().length, denominator.toString().length);
    const format = n => ("0".repeat(nDigits) + n).slice(-nDigits);
    return `${format(numerator)}/${format(denominator)}`;
}


export default SideBar;
