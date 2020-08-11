import {useState, useMemo, useRef} from 'react';

/*
 * A SpanManager that manages the state of spans (parts of a file that compare50 identifies).
 * This manager maps regions of a file to the spans identified by compare50.
 * A region is an object of the form:
 * {fileId: 1, start: 0, end: 10}
 */
class SpanManager {
    constructor(regionMap, ignoredRegionMap, spanStates, setSpanStates) {
        this.spans = regionMap.spans;
        this._regionMap = regionMap;

        this.ignoredSpans = ignoredRegionMap.spans;
        this._ignoredRegionMap = ignoredRegionMap;

        // An immutable map from spanId to state
        this._spanStates = spanStates;

        // Change _spanStates (triggers a rerender)
        this._setSpanStates = setSpanStates;
    }

    activate(region) {
        const groupId = this._regionMap.getGroupId(region);
        if (groupId === null) {
            return;
        }

        const spanStates = this.spans.reduce((acc, span) => {
            // Don't overwrite a selected span
            if (this.isSelected(span) || this.isHighlighted(span)) {
                acc[span.id] = this._getState(span);
            }
            // Set all spans in group to
            else if (span.groupId === groupId) {
                acc[span.id] = Span.STATES.ACTIVE;
            }
            // Set everything else to inactive
            else {
                acc[span.id] = Span.STATES.INACTIVE;
            }

            return acc;
        }, {});

        this._setSpanStates(spanStates);
    }

    select(region) {
        const groupId = this._regionMap.getGroupId(region);
        if (groupId === null) {
            return;
        }

        // If this span was selected before, highlight the next span in the other sub
        if (this.isHighlighted(region)) {
            this._reselect(region);
            return;
        }

        // Grab the span that is selected
        const selectedSpan = this._regionMap.getSpan(region);

        // Grab all spans in the same group
        const groupedSpans = this.spans.filter(span => span.groupId === selectedSpan.groupId);

        // Keep track of whether the first span in the other sub has been found
        let foundFirst = false;

        // Highlight the selected span, and the first in the other sub, select all other grouped spans
        let spanStates = groupedSpans.reduce((acc, span) => {
            if (span === selectedSpan) {
                acc[span.id] = Span.STATES.HIGHLIGHTED;
            }
            else if (!foundFirst && span.subId !== selectedSpan.subId) {
                acc[span.id] = Span.STATES.HIGHLIGHTED;
                foundFirst = true;
            }
            else {
                acc[span.id] = Span.STATES.SELECTED;
            }
            return acc;
        }, {});

        // Set all other spans to inactive
        spanStates = this.spans.reduce((acc, span) => {
            if (!acc.hasOwnProperty(span.id)) {
                acc[span.id] = Span.STATES.INACTIVE;
            }
            return acc;
        }, spanStates);

        this._setSpanStates(spanStates);
    }

    _reselect(region) {
        // Find which span was reselected
        const selectedSpan = this._regionMap.getSpan(region);

        // Grab all spans from the other submission in the same group
        const groupedSpans = this.spans.filter(span => span.groupId === selectedSpan.groupId);

        // Grab all spans from the group in the other submission
        const otherSpans = groupedSpans.filter(span => span.subId !== selectedSpan.subId);

        // Find which span from the other submission was highlighted before
        const highlightedSpan = otherSpans.filter(span =>this.isHighlighted(span))[0];

        // Find which span should now be highlighted
        const newIndex = (otherSpans.indexOf(highlightedSpan) + 1) % otherSpans.length;
        const newHighlightedSpan = otherSpans[newIndex];

        // Create the state for each span from the other submission
        let spanStates = groupedSpans.reduce((acc, span) => {
            if (span === newHighlightedSpan || span === selectedSpan) {
                acc[span.id] = Span.STATES.HIGHLIGHTED;
            } else {
                acc[span.id] = Span.STATES.SELECTED;
            }
            return acc;
        }, {});

        // Set all other spans to inactive
        spanStates = this.spans.reduce((acc, span) => {
            if (!acc.hasOwnProperty(span.id)) {
                acc[span.id] = Span.STATES.INACTIVE;
            }
            return acc;
        }, spanStates);

        this._setSpanStates(spanStates);
    }

    selectNextGroup() {
        this._selectAdjacentGroup(1);
    }

    selectPreviousGroup() {
        this._selectAdjacentGroup(-1);
    }

    isFirstInSpan(region) {
        return this._regionMap.getSpan(region).start === region.start;
    }

    isHighlighted(region) {
        return this._getState(region) === Span.STATES.HIGHLIGHTED;
    }

    isActive(region) {
        return this._getState(region) === Span.STATES.ACTIVE;
    }

    isSelected(region) {
        return this._getState(region) === Span.STATES.SELECTED;
    }

    isGrouped(region) {
        return this._regionMap.getGroupId(region) !== null;
    }

    isIgnored(region) {
        return this._ignoredRegionMap.getSpan(region) !== null;
    }

    selectedGroupId() {
        for (let span of this.spans) {
            if (this._spanStates[span.id] === Span.STATES.SELECTED || this._spanStates[span.id] === Span.STATES.HIGHLIGHTED) {
                return span.groupId;
            }
        }
        return 0;
    }

    nGroups() {
        return this._regionMap.nGroups;
    }

    _selectAdjacentGroup(direction) {
        let groupId = this.selectedGroupId();

        // increment index
        groupId += direction;

        // wrap around
        if (groupId > this.nGroups()) {
            groupId = 1;
        }
        else if (groupId < 1) {
            groupId = this.nGroups();
        }


        for (let span of this.spans) {
            if (span.groupId === groupId) {
                this.select(span);
                return;
            }
        }
    }

    _getState(region) {
        const span = this._regionMap.getSpan(region);

        if (span === null) {
            return Span.STATES.INACTIVE;
        }

        return this._spanStates[span.id];
    }
}


// Immutable map from a region in a file to a span/group
class RegionMap {
    constructor(spans) {
        this.spans = spans;

        // Memoization map, maps a this._key() to a span
        this._map = {};

        this.nGroups = new Set(this.spans.map(span => span.groupId)).size;
    }

    getSpan(region) {
        const key = this._key(region);

        // Get span from memory if possible
        if (this._map[key] !== undefined) {
            return this._map[key];
        }

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

        // Memoize span
        this._map[key] = largestSpan;

        return largestSpan;
    }

    getGroupId(region, state) {
        const span = this.getSpan(region);
        return span !== null ? span.groupId : null;
    }

    _key(region) {
        return `${region.fileId}:${region.start}`;
    }
}


class Span {
    static STATES = {
        INACTIVE: 0,
        ACTIVE: 1,
        SELECTED: 2,
        HIGHLIGHTED: 3
    }

    constructor(id, subId, fileId, groupId, start, end, isIgnored=false) {
        this.id = id;
        this.subId = subId;
        this.fileId = fileId;
        this.groupId = groupId;
        this.start = start;
        this.end = end;
        this.isIgnored = isIgnored;
    }
}


function useSpanManager(pass) {
    const initSpans = () => {
        const spans = [];
        pass.spans.forEach(span => {
            if (!span.ignored) {
                const groupId = pass.groups.find(group => group.spans.includes(span.id)).id;
                spans.push(new Span(span.id, span.subId, span.fileId, groupId, span.start, span.end, span.ignored));
            }
        });
        return spans;
    }

    const initIgnoredSpans = () =>
        pass.spans.filter(span => span.ignored).map(span => new Span(span.id, span.subId, span.fileId, null, span.start, span.end, span.ignored));

    const initSpanStates = () => {
        const spanStates = spans.reduce((acc, span) => {
            acc[span.id] = Span.STATES.INACTIVE;
            return acc;
        }, {});

        return spanStates;
    }

    const unselectSpanStates = spanStates => {
        Object.keys(spanStates).forEach(spanId => {
            if (spanStates[spanId] === Span.STATES.SELECTED || spanStates[spanId] === Span.STATES.HIGHLIGHTED) {
                spanStates[spanId] = Span.STATES.INACTIVE;
            }
        });
        return spanStates;
    }

    // Memoize the (expensive) mapping from regions to spans on the selected pass
    const spans = useMemo(initSpans, [pass.name]);
    const regionMap = useMemo(() => new RegionMap(spans), [spans]);

    // Memoize the (expensive) mapping from regions to ignoredSpans on the selected pass
    const ignoredSpans = useMemo(initIgnoredSpans, [pass.name]);
    const ignoredRegionMap = useMemo(() => new RegionMap(ignoredSpans), [spans]);

    // A map from pass.name => span.id => state
    const [allSpanStates, setAllSpanStates] = useState({});

    // Keep track of the last pass
    const passRef = useRef(pass);

    // Retrieve the spanStates from the map, otherwise create new
    let spanStates = allSpanStates[pass.name]
    if (spanStates === undefined) {
        spanStates = initSpanStates();
    }

    // In case pass changed, unselect everything in the new pass
    if (passRef.current !== pass) {
        passRef.current = pass;
        spanStates = unselectSpanStates(spanStates);
    }

    // Callback to set the spanStates for the current pass
    const setSpanStates = spanStates => {
        const temp = {}
        temp[pass.name] = {...(allSpanStates[pass.name]), ...spanStates}
        setAllSpanStates({...allSpanStates, ...temp})
    };

    return new SpanManager(regionMap, ignoredRegionMap, spanStates, setSpanStates);
}


export {Span}
export default useSpanManager
