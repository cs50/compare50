import React from 'react';
import "./table.css";

function ArchiveImg() {
    const style = {"fill": "rgba(216, 216, 216, 0)", "stroke": "rgb(0, 0, 0)", "stroke-width": "2px;"};

    return (
        <svg viewBox="79.164 91.172 63.675 66.68" width="1.5em" height="1.5em" xmlns="http://www.w3.org/2000/svg" xmlnsBx="https://boxy-svg.com">
            <path style={style} d="M 89.898 99.084 H 131.124 A 4.5 4.467 0 0 1 135.624 103.551 V 106.018 A 2 2 0 0 1 133.624 108.018 H 87.398 A 2 2 0 0 1 85.398 106.018 V 103.551 A 4.5 4.467 0 0 1 89.898 99.084 Z" bxShape="rect 85.398 99.084 50.226 8.934 4.5 4.5 2 2 1@72b6ad5a"/>
            <rect x="90.259" y="113.324" width="40.503" height="34.631" style={style}/>
            <rect style={style} x="102.169" y="119.696" width="16.684" height="3.633" rx="1" ry="1"/>
        </svg>
    )
}


const defaultMatchTableRowCallbacks = {
    mouseenter: () => null,
    mouseleave: () => null
}

const defaultMatchTableRowSubmission = {
    id: -1,
    isArchive: false,
    isHighlighted: false,
    isSelected: false
}

function MatchTableRow({
    index = -1,
    subA = defaultMatchTableRowSubmission,
    subB = defaultMatchTableRowSubmission,
    score = -1,
    color = "#ffb74d",
    callbacks = defaultMatchTableRowCallbacks,
}) {
    const firstTdStyle = {
        borderLeftColor: color,
        borderLeftWidth: "10px",
        borderLeftStyle: "solid",
        width: "5em"
    }

    const lastTdStyle = {
        borderRightColor: color,
        borderRightWidth: "10px",
        borderRightStyle: "solid",
        width: "5em"
    };

    const styleSub = (sub) => {
        const style = {};
        if (sub.isHighlighted) {
            style.backgroundColor = "#ffe0b2";
        }
        if (sub.isSelected) {
            style.color = "white";
            style.backgroundColor = "#ffb74d";
        }
        return style;
    }

    const roundedScore = Math.round(score * 10) / 10;

    return (
        <tr
            key={index}
            onClick={() => window.location.href = "match_" + (index) + ".html"}
            onMouseEnter={callbacks.mouseenter}
            onMouseLeave={callbacks.mouseleave}
        >
            <td style={firstTdStyle}>{index}</td>
            <td style={styleSub(subA)} data-tip={subA.id}>{subA.id}{subA.isArchive && <ArchiveImg/>}</td>
            <td style={styleSub(subB)} data-tip={subB.id}>{subB.id}{subB.isArchive && <ArchiveImg/>}</td>
            <td style={lastTdStyle}>{roundedScore}</td>
        </tr>
    );
}


const defaultMatchTableGraph = {
    links: [],
    nodes: []
}

const defaultMatchTableHighlighted = {
    nodes: [],
    group: -1
}

const defaultMatchTableCallbacks = {
    mouseenter: ({
        submissionA = null,
        submissionB = null,
        group = -1
    }) => null,
    mouseleave: (event) => null
}

function MatchTable({
    graph = defaultMatchTableGraph,
    selected = null,
    highlighted = defaultMatchTableHighlighted,
    callbacks = defaultMatchTableCallbacks,
    cutoff = 0
}) {
    // maps from a node.id to a node
    const nodeMap = {}
    graph.nodes.forEach(node => {
        nodeMap[node.id] = node;
    })

    class MatchTableRowSubmission {
        constructor(node) {
            this.id = node.id;
            this.isArchive = nodeMap[node.id].isArchive;
            this.isSelected = selected !== null && selected.id === node.id;
            this.isHighlighted = highlighted !== null && highlighted.nodes.length === 1 && highlighted.nodes.includes(node.id);
        }
    }

    const rows = graph.links.filter(link => {
        const group = nodeMap[link.nodeAId].group;
        
        // hide anything below the cutoff threshold and anything that isn't selected
        return link.value >= cutoff && (selected === null || selected.group === group);        
    }).map(link => {
        const subA = new MatchTableRowSubmission(nodeMap[link.nodeAId]);
        const subB = new MatchTableRowSubmission(nodeMap[link.nodeBId]);

        return <MatchTableRow 
            key={link.index}
            subA={subA}
            subB={subB}
            index={link.index + 1}
            score={link.value}
            color={nodeMap[subA.id].color} 
            callbacks={{
                "mouseenter": () => callbacks.mouseenter({
                    submissionA: subA.id,
                    submissionB: subB.id,
                    group: nodeMap[link.nodeAId].group
                }),
                "mouseleave": callbacks.mouseleave
            }}
        />
    });

    return (
        <table className="styled-table">
            <thead>
                <tr>
                    <th>#</th>
                    <th colSpan="2">Submissions</th>
                    <th colSpan="2">Score <span data-tip="Similarity of submissions on a relative scale from 1 to 10." className="tooltip-marker">?</span></th>
                </tr>
            </thead>
            <tbody>
                {rows}
            </tbody>
        </table>
    );
}

export default MatchTable;
