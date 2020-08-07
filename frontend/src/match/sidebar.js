import React, {useRef, useEffect} from 'react';

import Graph from '../home/graph';

import './matchview.css';
import './sidebar.css';


function SideBar(props) {
    let style = {
        "margin": "auto",
        "marginBottom": ".5em",
        "marginTop": ".5em",
        "width": "90%"
    }

    const updateGlobalState = newState => props.setGlobalState({...props.globalState, ...newState})

    return (
        <div className="column-box">
            <div className="row auto" style={style}>
                <MatchNavigation
                    current={props.globalState.currentMatch}
                    n={props.globalState.nMatches}
                    setMatch={match => updateGlobalState({"currentMatch": match})}
                />
            </div>
            <div className="row auto" style={style}>
                <PassNavigation
                    passes={props.globalState.passes}
                    currentPass={props.globalState.currentPass}
                    setPass={pass => updateGlobalState({"currentPass": pass})}
                />
            </div>
            <div className="row auto" style={style}>
                <GroupNavigation
                    spanManager={props.spanManager}
                    setGroup={group => updateGlobalState({"currentGroup": group})}
                />
            </div>
            <div className="row auto" style={style}>
                <ConfigMenu
                    softWrap={props.globalState.softWrap}
                    setSoftWrap={softWrap => updateGlobalState({"softWrap": softWrap})}
                    hideIgnored={props.globalState.hideIgnored}
                    setHideIgnored={hideIgnored => updateGlobalState({"hideIgnored": hideIgnored})}
                    showWhiteSpace={props.globalState.showWhiteSpace}
                    setShowWhiteSpace={showWhiteSpace => updateGlobalState({"showWhiteSpace": showWhiteSpace})}
                />
            </div>
            <div className="row auto" style={style}>
                <ExportMenu/>
            </div>
            <div className="row fill" style={style}>
                <Graph graph={props.graphData} slider={false} sliderTip={false}/>
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
                <span className="btn">
                    <button type="button" style={{"width":"50%"}}>{"<<"}</button>
                </span>
                <span className="btn">
                    <button type="button" style={{"width":"50%"}}>{">>"}</button>
                </span>
            </div>
        </div>
    )
}


function PassNavigation(props) {
    return (
        <div className="btn-group vertical">
            {props.passes.map((pass, i) =>
                <PassButton
                    pass={pass}
                    index={i + 1}
                    isSelected={props.currentPass.name === pass.name}
                    key={`pass_${pass.name}`}
                    setPass={props.setPass}
                />
            )}
        </div>
    )
}


function PassButton(props) {
    useEffect(() => {
        const eventListener = (event) =>  {
            if (event.key === props.index.toString()) {
                event.preventDefault();
                props.setPass(props.pass);
            }
        };

        document.addEventListener("keyup", eventListener);

        return () => document.removeEventListener("keyup", eventListener);
    });

    return (
        <span className="tooltip btn">
            <button
                className={`monospace-text ${props.isSelected ? " active" : ""}`}
                type="button"
                title={props.pass.docs}
                style={{"width":"100%"}}
                onClick={() => {props.setPass(props.pass)}}
            >
                {props.pass.name}
            </button>
            <ShortcutTooltip shortcut={props.index.toString()}/>
        </span>
    )
}



function GroupNavigation(props) {
    const prevRef = useRef(null);
    const nextRef = useRef(null);

    useEffect(() => {
        const eventListener = (event) =>  {
            if (event.key.toLowerCase() === "e") {
                event.preventDefault();
                nextRef.current.click();
            }
            else if (event.key.toLowerCase() === "q") {
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
                <span className="btn">
                    <button
                        className="btn"
                        ref={prevRef}
                        type="button"
                        style={{"width":"50%"}}
                        onClick={() => props.spanManager.selectPreviousGroup()}
                    >
                        &lt;
                    </button>
                </span>
                <ShortcutTooltip shortcut="q e" position="bottom"/>
                <span className="btn">
                    <button
                        className="btn"
                        ref={nextRef}
                        type="button"
                        style={{"width":"50%"}}
                        onClick={() => props.spanManager.selectNextGroup()}
                    >
                        &gt;
                    </button>
                </span>
            </div>
        </div>
    )
}


function ExportMenu(props) {
    return (
        <div className="btn-group vertical">
            <span className="btn tooltip">
                <button type="button" style={{"width":"100%"}}>PDF</button>
                <span className="tooltiptext">{"Export both submissions side-by-side as PDF"}</span>
            </span>
        </div>
    )
}


function ConfigMenu(props) {
    return (
        <React.Fragment>
            <div style={{"marginBottom": ".25em"}}>
                <Switch text="wrap" default={props.softWrap} setOption={props.setSoftWrap} tooltip="Soft Wrap long lines of code"/>
            </div>
            <div style={{"marginBottom": ".25em"}}>
                <Switch text="hide" default={props.hideIgnored} setOption={props.setHideIgnored} tooltip="Hide code that was not used in the comparison"/>
            </div>
            <div>
                <Switch text="&nbsp;WS&nbsp;" default={props.showWhiteSpace} setOption={props.setShowWhiteSpace} tooltip="Show leading whitespace"/>
            </div>
        </React.Fragment>
    )
}


function ShortcutTooltip(props) {
    return (
        <span className={`tooltiptext ${props.position}`}>
            <span>Press </span>
            <span className="monospace-text" style={{"fontWeight":"bold"}}>{props.shortcut}</span>
        </span>
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
                <span className="tooltiptext">{props.tooltip}</span>
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
