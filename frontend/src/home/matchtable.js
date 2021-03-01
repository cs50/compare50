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


function MatchTableRow(props) {
    const firstTdStyle = {
        borderLeftColor: props.color,
        borderLeftWidth: "10px",
        borderLeftStyle: "solid"
    }

    const lastTdStyle = {
        borderRightColor: props.color,
        borderRightWidth: "10px",
        borderRightStyle: "solid"
    };

    const aStyle = {};
    const bStyle = {};

    const subA = props.subA;
    const subB = props.subB;

    if (subA.isHighlighted) {
        aStyle.backgroundColor = "#ffe0b2";
    }
    if (subB.isHighlighted) {
        bStyle.backgroundColor = "#ffe0b2";
    }

    if (subA.isSelected) {
        aStyle.color = "white";
        aStyle.backgroundColor = "#ffb74d";
    }
    if (subB.isSelected) {
        bStyle.color = "white";
        bStyle.backgroundColor = "#ffb74d";
    }

    const score = Math.round(props.score * 10) / 10;

    return (
        <tr
            key={props.index}
            onClick={() => window.location.href = "match_" + (props.index + 1) + ".html"}
            onMouseEnter={props.callbacks.mouseenter}
            onMouseLeave={props.callbacks.mouseleave}
        >
            <td style={firstTdStyle}>{props.index + 1}</td>
            <td style={aStyle} data-tip={subA.id}>{subA.id}{subA.isArchive && <ArchiveImg/>}</td>
            <td style={bStyle} data-tip={subB.id}>{subB.id}{subB.isArchive && <ArchiveImg/>}</td>
            <td style={lastTdStyle}>{score}</td>
        </tr>
    );
}


function MatchTable(props) {
    const graph = props.graph;

    // maps from a node.id to groupIds, colors and whether that node is an Archive
    const nodeGroups = {};
    const nodeColors = {};
    const nodeArchives = {};
    graph.nodes.forEach(n => {
        nodeGroups[n.id] = n.group;
        nodeColors[n.id] = n.color;
        nodeArchives[n.id] = n.isArchive;
    });

    const selected = props.selected;
    const highlighted = props.highlighted;

    class MatchTableRowSubmission {
        constructor(node) {
            this.id = node.id;
            this.isArchive = nodeArchives[node.id];
            this.isSelected = selected !== null && selected.id === node.id;
            this.isHighlighted = highlighted !== null && highlighted.nodes.length === 1 && highlighted.nodes.includes(node.id);
        }
    }

    const rows = graph.links.map(link => {
        const group = nodeGroups[link.source.id];
        
        // if there is a group selected, hide any matches not in that group
        if (selected !== null && selected.group !== group) {
            return;
        }

        const subA = new MatchTableRowSubmission(link.source);
        const subB = new MatchTableRowSubmission(link.target);

        return <MatchTableRow 
            key={link.index}
            subA={subA}
            subB={subB}
            index={link.index}
            score={link.value}
            color={nodeColors[subA.id]} 
            callbacks={{
                "mouseenter": () => props.callbacks.mouseenter({
                    submissionA: subA.id,
                    submissionB: subB.id,
                    group: group
                }),
                "mouseleave": props.callbacks.mouseleave
            }}
        />
    });

    return (
        <table className="styled-table">
            <thead>
                <tr>
                    <th>#</th>
                    <th colSpan="2">Submissions</th>
                    <th colSpan="2">Score <span data-tip="On a scale of 1-10, how similar the files are." className="tooltip-marker">?</span></th>
                </tr>
            </thead>
            <tbody>
                {rows}
            </tbody>
        </table>
    );
}

export default MatchTable;
