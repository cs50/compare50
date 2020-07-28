import React, {useState, useMemo} from 'react';


class SpanManager {
    constructor(spans, spanStates, setSpanStates, regionMap) {
        this.spans = spans;

        // An immutable map from spanId to state
        this._spanStates = spanStates;

        // Change _spanStates (triggers a rerender)
        this._setSpanStates = setSpanStates;

        this._regionMap = regionMap;
    }

    activate(region) {
        const groupId = this._regionMap.getGroupId(region);
        if (groupId === null) {
            return;
        }

        const spanStates = this.spans.reduce((acc, span) => {
            // Don't overwrite a selected span
            if (this._spanStates[span.id] === Span.STATES.SELECTED) {
                acc[span.id] = Span.STATES.SELECTED;
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

        const spanStates = this.spans.reduce((acc, span) => {
            // Set all spans in group to
            if (span.groupId === groupId) {
                acc[span.id] = Span.STATES.SELECTED;
            }
            // Set everything else to inactive
            else {
                acc[span.id] = Span.STATES.INACTIVE;
            }
            return acc;
        }, {});

        this._setSpanStates(spanStates);
    }

    selectNextGroup() {
        this._selectAdjacentGroup(1);
    }

    selectPreviousGroup() {
        this._selectAdjacentGroup(-1);
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

    selectedGroupIndex() {
        for (let span of this.spans) {
            if (this._spanStates[span.id] === Span.STATES.SELECTED) {
                return span.groupId + 1;
            }
        }
        return 1;
    }

    nGroups() {
        return this._regionMap.nGroups;
    }

    _selectAdjacentGroup(direction) {
        let groupIndex = this.selectedGroupIndex();

        // increment index
        groupIndex += direction;

        // wrap around
        if (groupIndex > this.nGroups()) {
            groupIndex = 1;
        }
        else if (groupIndex < 1) {
            groupIndex = this.nGroups();
        }

        const groupId = groupIndex - 1;

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
        SELECTED: 2
    }

    constructor(id, fileId, groupId, start, end, isIgnored=false) {
        this.id = id;
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
        pass.groups.forEach((group, groupId) => {
            group.forEach(span => {
                spans.push(new Span(span.id, span.fileId, groupId, span.start, span.end));
            });
        });
        return spans;
    }
    // TODO ignored spans

    // Memoize the (expensive) mapping from regions to spans on the selected pass
    const spans = useMemo(initSpans, [pass.pass]);
    const regionMap = useMemo(() => new RegionMap(spans, pass.groups), [pass.pass]);

    const [spanStates, setSpanStates] = useState(spans.reduce((acc, span) => {
        acc[span.id] = Span.STATES.INACTIVE;
        return acc;
    }, {}));

    return [new SpanManager(spans, spanStates, setSpanStates, regionMap)];
}

export {SpanManager, Span, RegionMap}
export default useSpanManager
