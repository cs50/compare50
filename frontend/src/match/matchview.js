import React, {useState} from 'react';

import './matchview.css';
import SideBar from './sidebar';
import SplitView from './code/splitview';

import API from '../api';
import useSpanManager from './spanmanager';


function MatchView() {
    const getData = function() {
        setGlobalState({
            ...globalState,
            ...{"isDataLoaded": null}
        })

        Promise.all([
            API.getMatch(),
            API.getGraph()
        ])
        .then(([match, graph]) => {
            setGraph(graph);
            setMatch(match);
            setGlobalState({
                ...globalState,
                ...{"passes": match.passes,
                    "currentPass": match.passes[0],
                    "isDataLoaded": true
                }
            });
        });
    }

    const [globalState, setGlobalState] = useState({
        "currentPass": {
            "name": "",
            "docs": "",
            "score": "",
            "spans": [],
            "groups": []
        },
        "passes": [],
        "nMatches": 50,
        "currentMatch": 1,
        "softWrap": true,
        "showWhiteSpace": false,
        "isDataLoaded": false
    });

    const [match, setMatch] = useState({
        "filesA": () => [],
        "filesB": () => []
    });

    const [graphData, setGraph] = useState({});

    if (globalState.isDataLoaded === false) {
        getData();
    }

    const spanManager = useSpanManager(globalState.currentPass, match);

    return (
        <div className="row-box" style={{"height":"100vh"}}>
          <div className="row auto" style={{"width":"9em"}}>
              <div className="column-box" style={{"borderRight": "1px solid #a7adba"}}>
                  <div className="row fill">
                      <SideBar globalState={globalState} setGlobalState={setGlobalState} match={match} spanManager={spanManager} graphData={graphData}/>
                  </div>
              </div>
          </div>
          <div className="row fill">
              <SplitView topHeight="2.5em" globalState={globalState} match={match} spanManager={spanManager}/>
          </div>
        </div>
    );
}


export default MatchView;
