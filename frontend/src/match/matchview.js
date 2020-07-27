import React, {useState} from 'react';

import './matchview.css';
import SideBar from './sidebar';
import Logo from './logo';
import SplitView from './code/splitview';

import API from '../api';


function MatchView() {
    const [globalState, setGlobalState] = useState({
        "currentPass": API.getPasses()[0],
        "passes": API.getPasses(),
        "nMatches": 50,
        "currentMatch": 1,
        "currentGroup": 1,
        "nGroups": 6,
        "softWrap": true
    });

    const [match] = useState(API.getMatch());

    const [regionMap] = usePass(API.getMatch().getPass("structure"));

    return (
        <div className="row-box" style={{"height":"100vh"}}>
          <div className="row auto" style={{"width":"9em"}}>
              <div className="column-box" style={{"borderRight": "1px solid #a7adba"}}>
                  <div className="row auto">
                      <Logo height="2.5em"/>
                  </div>
                  <div className="row fill">
                      <SideBar globalState={globalState} setGlobalState={setGlobalState}/>
                  </div>
              </div>
          </div>
          <div className="row fill">
              <SplitView topHeight="2.5em" globalState={globalState} match={match} regionMap={regionMap}/>
          </div>
        </div>
    );
}


class RegionMap {
    constructor(spans, groups, setSpans) {
        this.spans = spans;
        this._groups = groups;
        this._setSpans = setSpans;
    }

    update(region, state) {
        const groupId = this._getGroupId(region);
        if (groupId === null) {
            return;
        }

        const spans = this.spans.map((span, i) => {
            if (span.groupId === groupId) {
                return span.setState(state);
            } else {
                return span.setState(Span.STATES.INACTIVE);
            }
        });

        this._setSpans(spans);
    };

    activate(region) {
        this.update(region, Span.STATES.ACTIVE);
    }

    select(region) {
        this.update(region, Span.STATES.SELECT);
    }

    isActive(region) {
        const span = this._getSpan(region);
        let result = span !== null && span.state === Span.STATES.ACTIVE;
        return result
    }

    isSelected(region) {
        const span = this._getSpan(region);
        return span !== null && span.state === Span.STATES.SELECTED;
    }

    isGrouped(region) {
        return this._getGroupId(region) !== null;
    }

    _getGroupId(region) {
        const span = this._getSpan(region);
        return span !== null ? span.groupId : null;
    }

    _getSpan(region) {
        // TODO likely candidate for optimization, memoization might be good enough, KISS for now
        let largestSpan = null;

        this.spans.forEach(span => {
            // span is from the same file, and starts and finishes before region
            const contains = span.fileId === region.fileId && span.start <= region.start && span.end >= region.end;

            // The largest span takes priority
            const isLargest = largestSpan === null || largestSpan.end - largestSpan.start < span.end - span.start;

            if (contains && isLargest) {
                largestSpan = span;
            }
        });

        return largestSpan;
    }
}


class Span {
    static STATES = {
        INACTIVE: 0,
        ACTIVE: 1,
        SELECTED: 2
    }

    constructor(fileId, groupId, start, end, isIgnored=false) {
        this.fileId = fileId;
        this.groupId = groupId;
        this.start = start;
        this.end = end;
        this.state = Span.STATES.INACTIVE;
        this.isIgnored = isIgnored;
    }

    setState(state) {
        let span = new Span(this.fileId, this.groupId, this.start, this.end, this.isIgnored);
        span.state = state;
        return span;
    }
}


function usePass(pass) {
    const initSpans = () => {
        const spans = [];
        pass.groups.forEach((group, groupId) => {
            group.forEach(span => {
                spans.push(new Span(span.fileId, groupId, span.start, span.end));
            });
        });
        return spans
    }
    // TODO ignored spans

    const [spans, setSpans] = useState(initSpans());

    return [new RegionMap(spans, pass.groups, setSpans)];
}


export {Span};
export default MatchView;
