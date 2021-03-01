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


class MatchTableRow extends React.Component {
    callbacks = {
        mouseenter: () => {
            this.props.callbacks.mouseenter({link: this.props.link, group: this.props.nodeGroup});
        }
    }

    goTo = () => {
        window.location.href = "match_" + this.props.link.link_index + ".html";
    }

    render() {
        const firstTdStyle = {
            borderLeftColor: this.props.color,
            borderLeftWidth: "10px",
            borderLeftStyle: "solid"
        }

        const lastTdStyle = {
            borderRightColor: this.props.color,
            borderRightWidth: "10px",
            borderRightStyle: "solid"
        };

        let trStyle = {}, sourceStyle = {}, targetStyle = {};
        if (this.props.highlight !== null) {
            const hl = this.props.highlight;
            const sourceIsHighlighted = !hl.clicked && hl.id === this.props.link.source.id;
            const targetIsHighlighted = !hl.clicked && hl.id === this.props.link.target.id

            trStyle.backgroundColor = !hl.clicked && hl.group === this.props.nodeGroup ? "#ececec" : undefined;
            if (sourceIsHighlighted) {
                sourceStyle.backgroundColor = "#ffe0b2";
            }
            if (targetIsHighlighted) {
                targetStyle.backgroundColor = "#ffe0b2";
            }
        }

        if (this.props.selected !== null) {
            const sl = this.props.selected;
            const targetIsSelected = sl.id === this.props.link.target.id;
            const sourceIsSelected = sl.id === this.props.link.source.id; 

            sourceStyle.color = sourceIsSelected ? "white" : undefined;
            sourceStyle.backgroundColor = sourceIsSelected ? "#ffb74d" : sourceStyle.backgroundColor;
            targetStyle.color = targetIsSelected ? "white" : undefined;
            targetStyle.backgroundColor = targetIsSelected ? "#ffb74d" : targetStyle.backgroundColor;
        }

        return (
            <tr
                style={trStyle}
                key={this.props.link.index}
                onClick={this.goTo}
                onMouseEnter={this.callbacks.mouseenter}
                onMouseLeave={this.props.callbacks.mouseleave}
            >
                <td style={firstTdStyle}>{this.props.link.index + 1}</td>
                <td style={sourceStyle} data-tip={this.props.link.source.id}>{this.props.link.source.id}{this.props.sourceIsArchive && <ArchiveImg/>}</td>
                <td style={targetStyle} data-tip={this.props.link.target.id}>{this.props.link.target.id}{this.props.targetIsArchive && <ArchiveImg/>}</td>
                <td style={lastTdStyle}>{Math.round(this.props.link.value * 10) / 10}</td>
            </tr>
        );
    }
}

class MatchTable extends React.Component {
    callbacks = {
        mouseenter: (evt) => {
            this.props.callbacks.mouseenter(evt)
        },
        mouseleave: this.props.callbacks.mouseleave
    }

    render() {
        const graph = this.props.graph;
        const nodeGroups = {};
        const nodeColors = {};
        const nodeArchives = {};

        graph.nodes.forEach(n => {
            nodeGroups[n.id] = n.group;
            nodeColors[n.id] = n.color;
            nodeArchives[n.id] = n.isArchive;
        });

        let rows = graph.links.map(link => 
            <MatchTableRow 
                link={link}
                key={link.index}
                sourceIsArchive={nodeArchives[link.source.id]}
                targetIsArchive={nodeArchives[link.target.id]}
                color={nodeColors[link.source.id]} 
                callbacks={this.callbacks} 
                nodeGroup={nodeGroups[link.source.id]} 
                highlight={this.props.highlight} 
                selected={this.props.selected}
            />
        )

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
}

export default MatchTable;
