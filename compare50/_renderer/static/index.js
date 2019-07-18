const ARCHIVE_IMG = `<?xml version="1.0" encoding="utf-8"?>
<svg viewBox="79.164 91.172 63.675 66.68" width=1.5em height=1.5em xmlns="http://www.w3.org/2000/svg" xmlns:bx="https://boxy-svg.com">
  <path style="fill: rgba(216, 216, 216, 0); stroke: rgb(0, 0, 0); stroke-width: 2px;" d="M 89.898 99.084 H 131.124 A 4.5 4.467 0 0 1 135.624 103.551 V 106.018 A 2 2 0 0 1 133.624 108.018 H 87.398 A 2 2 0 0 1 85.398 106.018 V 103.551 A 4.5 4.467 0 0 1 89.898 99.084 Z" bx:shape="rect 85.398 99.084 50.226 8.934 4.5 4.5 2 2 1@72b6ad5a"/>
  <rect x="90.259" y="113.324" width="40.503" height="34.631" style="fill: rgba(216, 216, 216, 0); stroke: rgb(0, 0, 0); stroke-width: 2px;"/>
  <rect style="fill: rgb(255, 255, 255); stroke: rgb(0, 0, 0); stroke-width: 2px;" x="102.169" y="119.696" width="16.684" height="3.633" rx="1" ry="1"/>
</svg>`

var RADIUS = 10;
var WIDTH = null;
var HEIGHT = null;

var SVG = null
var SLIDER = null;
var G_NODE = null;
var G_LINK = null;

var NODE_DATA = GRAPH.nodes;
var LINK_DATA = GRAPH.links;

var COLOR = null;

// When there are exactly two nodes in the graph, d3 sets all kinds of things to
// NaN for an unknown reason
// This bool exists to mark all the places in the code where we implement the hack to fix this issue.
const HORRIBLE_TWO_NODE_HACK = true;

function init_data() {
    if (HORRIBLE_TWO_NODE_HACK) {
        /// When there are exactly two nodes, add an additional one with an id of "" and an edge with value -1
        if (GRAPH.nodes.length == 2) {
            GRAPH.nodes.push({id: ""});
            GRAPH.links.push({source: GRAPH.nodes[0], target: "", value: -1});
            GRAPH.data[""] = {is_archive: false};
        }
    }

    // simulation
    SIMULATION = d3.forceSimulation()
        .force("link", d3.forceLink().id(d => d.id))
        .force("charge", d3.forceManyBody().strength(-200).distanceMax(50).distanceMin(10))
        .force('collision', d3.forceCollide().radius(d => RADIUS * 2));

    SIMULATION
        .nodes(NODE_DATA);

    SIMULATION.force("link")
        .links(LINK_DATA);


    // assign groups to nodes
    let group_map = get_group_map(GRAPH.links.map(d => ({source:d.source.id, target:d.target.id})));
    GRAPH.nodes.forEach(d => d.group = group_map[d.id]);

    // set COLOR (function from group => color)
    let n_groups = Math.max.apply(0, GRAPH.nodes.map(node => node.group));
    COLOR = d3.scaleSequential().domain([0, n_groups + 1]).interpolator(d3.interpolateRainbow);
}

function init_graph() {
    SVG = d3.select("div#cluster_graph").append("svg");

    // If svg is clicked, unselect node
    SVG.on("click", () => {
        GRAPH.nodes.forEach(node =>
            node.is_node_in_spotlight = node.is_node_in_background = node.is_node_focused = node.is_group_focused = node.is_group_selected = node.is_node_selected = false)
        update();
    });

    // Slider
    let slider_start = null;
    if (HORRIBLE_TWO_NODE_HACK) {
        // Since the hack adds an edge with weight -1, filter it out
        slider_start = Math.floor(Math.min(...LINK_DATA.map(d => d.value).filter(v => v >= 0)));
    } else {
        slider_start = Math.floor(Math.min(...LINK_DATA.map(d => d.value)))
    }

    SLIDER = d3
        .sliderBottom()
        .min(slider_start)
        .max(10)
        .tickFormat(d => {
            let num = d3.format(".1f")(d)
            let [whole, fraction] = num.split(".");
            return fraction === "0" ? whole : num;
        })
        .ticks(10 - slider_start + 1)
        .default(0)
        .fill("#2196f3")
        .on("onchange", cutoff)
        .handle(
            d3
              .symbol()
              .type(d3.symbolCircle)
              .size(200)()
        );
    d3.select("div#slider")
      .append("svg")
        .attr("height", 100)
        .attr("class", "mx-auto d-block")
      .append("g")
        .attr("transform", "translate(30,30)");

    G_LINK = SVG.append("g").attr("class", "links");

    G_NODE = SVG.append("g").attr("class", "nodes");



    // scale graph and slider
    on_resize();

    // add data to graph
    update_graph();

    let choseX = d3.randomUniform(WIDTH / 4, 3 * WIDTH / 4);
    let choseY = d3.randomUniform(HEIGHT / 4, 3 * HEIGHT / 4);
    let pos_map = []
    NODE_DATA.forEach(d => {
        if (pos_map[d.group] === undefined) {
            pos_map[d.group] = {
                x: choseX(),
                y: choseY()
            };
        }
    });

    SIMULATION.force("x", d3.forceX(d => pos_map[d.group].x).strength(0.2))
              .force("y", d3.forceY(d => pos_map[d.group].y).strength(0.2));

    setTimeout(() => SIMULATION.force("x", null).force("y", null), 300);
}


function init_index() {
    let table = d3.select("div#index").append("table")
        .attr("class", "table table-hover w-100")
        .attr("id", "results");

    let thead_tr = table.append("thead").append("tr");
    thead_tr.append("td")
        .attr("scope", "col")
        .text("#");
    thead_tr.append("td")
        .attr("scope", "col")
        .attr("colspan", 2)
        .text("Submissions");
    thead_tr.append("td")
        .attr("scope", "col")
        .text("Score");

    INDEX = table.append("tbody");

    update_index();
}


function on_resize() {
    let cluster_div = document.getElementById("cluster");
    let header_size = document.querySelector("thead").clientHeight;
    cluster_div.style.paddingTop = `${header_size}px`;

    WIDTH = get_real_width(document.getElementById("cluster"));

    SLIDER.width(Math.floor(0.8 * WIDTH) - 60);
    d3.select("div#slider")
      .attr("width", WIDTH)
        .select("svg")
          .attr("width", Math.floor(0.8 * WIDTH))

    d3.select("div#slider")
      .attr("width", WIDTH)
      .select("svg")
        .attr("width", Math.floor(0.8 * WIDTH))
        .select("g")
          .call(SLIDER);

    HEIGHT = window.innerHeight - document.getElementById("title").clientHeight
                                - document.getElementById("slider").clientHeight
                                - header_size;

    SVG.attr("width", WIDTH).attr("height", HEIGHT);

    jiggle();
}


function get_real_width(elem) {
    let style = getComputedStyle(elem);
    return elem.clientWidth - parseFloat(style.paddingLeft) - parseFloat(style.paddingRight);
}


function ticked(links, nodes) {
    nodes
        .attr("x", function(d) { return d.x = Math.max(RADIUS, Math.min(WIDTH - RADIUS * 3, d.x)); })
        .attr("y", function(d) { return d.y = Math.max(RADIUS, Math.min(HEIGHT - RADIUS * 3, d.y)); });

    links
        .attr("x1", function(d) { return d.source.x + RADIUS; })
        .attr("y1", function(d) { return d.source.y + RADIUS; })
        .attr("x2", function(d) { return d.target.x + RADIUS; })
        .attr("y2", function(d) { return d.target.y + RADIUS; });
}


let DRAG_TARGET = null;

function dragstarted(d) {
    if (!d3.event.active) SIMULATION.alphaTarget(0.15).restart();
    d.fx = d.x;
    d.fy = d.y;

    DRAG_TARGET = d;
}


function dragged(d) {
    d.fx = d3.event.x;
    d.fy = d3.event.y;
}


function dragended(d) {
    if (!d3.event.active) SIMULATION.alphaTarget(0);
    d.fx = null;
    d.fy = null;

    let drag_target = DRAG_TARGET;
    DRAG_TARGET = null;

    on_mouseout_node(drag_target);
}


function on_mouseover_node(d) {
    if (DRAG_TARGET !== null) {
      return;
    }

    GRAPH.nodes.forEach(node => {
        node.is_group_focused = node.group === d.group;
        node.is_node_focused = node.id === d.id;
    });

    update();
}


function on_mouseout_node(d) {
    if (DRAG_TARGET !== null) {
        return;
    }

    GRAPH.nodes.forEach(node => {
        node.is_group_focused = node.is_node_focused = false;
    });

    update();
}


function on_click_node(d) {
    GRAPH.nodes.forEach(node => {
        node.is_node_selected = node.is_node_focused = node.id === d.id;
        node.is_group_selected = node.is_group_focused = node.group === d.group;
    });

    update();

    d3.event.stopPropagation();
}


function get_group_map(links) {
    // create a map from node_id to node
    let group_map = {};
    links.forEach(d => {
        group_map[d.source] = null;
        group_map[d.target] = null;
    });

    // create a map from node.id to directly connected node.ids
    let link_map = {};
    links.forEach(d => {
        if (d.source in link_map) {
            link_map[d.source].push(d.target);
        } else {
            link_map[d.source] = [d.target];
        }

        if (d.target in link_map) {
            link_map[d.target].push(d.source);
        } else {
            link_map[d.target] = [d.source];
        }
    })

    let group_id = 0;
    let visited = new Set();
    let unseen = new Set(Object.keys(group_map));

    // visit all nodes
    while (unseen.size > 0) {
        // start with an unseen node
        let node = unseen.values().next().value;
        unseen.delete(node);

        // DFS for all reachable nodes, start with all directly reachable
        let stack = [node];
        while (stack.length > 0) {
            // take top node on stack
            let cur_node = stack.pop();

            // visit it, give it a group
            visited.add(cur_node);
            group_map[cur_node] = group_id;

            // add all directly reachable (and unvisited nodes) to stack
            let directly_reachable = link_map[cur_node].filter(n => unseen.has(n));
            stack = stack.concat(directly_reachable);

            // remove all directly reachable elements from unseen
            directly_reachable.forEach(n => unseen.delete(n));
        }

        group_id++;
    }

    return group_map;
}


function cutoff(n) {
    LINK_DATA = GRAPH.links.filter(d => (d.value) >= n);
    let node_ids = new Set(LINK_DATA.map(d => d.source.id).concat(LINK_DATA.map(d => d.target.id)));
    NODE_DATA = GRAPH.nodes.filter(d => node_ids.has(d.id));

    update();

    jiggle(.1);
}


function update() {
    update_index();
    update_graph();
}


function update_index() {
    let table_data = INDEX.selectAll("tr").data(LINK_DATA, d => d.index);

    let new_trs = table_data.enter().append("tr");

    new_trs.append("th")
        .attr("scope", "row")
        .text(d => d.index + 1);

    for (let field of ["source", "target"]) {
        new_trs.append("td")
            .attr("class", "sub_name")
            .datum(d => d[field])
            .html(d => GRAPH.data[d.id].is_archive ? `${ARCHIVE_IMG} ${d.id}` : d.id);
    }

    new_trs.append("td")
        .attr("class", "score")
        .text(d => d.value.toFixed(1))
        .style("border-right", d => d.source.group === undefined ? "" : `10px solid ${COLOR(d.source.group)}`);


    new_trs
        .on("mouseover", link => {
            GRAPH.nodes.forEach(node => {
                node.is_node_in_splotlight = node.id === link.source.id || node.id === link.target.id;
                node.is_node_in_background = node.group !== link.source.group;
            });
            update_graph();
        })
        .on("mouseout", link => {
            GRAPH.nodes.forEach(node => {
                node.is_node_in_splotlight = false;
                node.is_node_in_background = false;
            })
            update_graph();
       })
       .on("click", d => window.open(`match_${d.index + 1}.html`));

    let group_selected = undefined;
    GRAPH.nodes.forEach(node => group_selected = node.is_group_selected ? node.group : group_selected);

    table_data.merge(new_trs)
              .style("background-color", link => link.source.is_group_focused && !link.source.is_group_selected ? "#ECECEC" : "")
              .style("display", link => group_selected !== undefined && group_selected !== link.source.group ? "none" : "")
              .selectAll(".sub_name")
                .style("background-color", d => d.is_node_focused ? "#CCCCCC" : "")
                .style("font-weight", d => d.is_node_selected ? "bold" : "");

    table_data.exit().remove();
}


function update_graph() {
    let links = G_LINK.selectAll("line").data(LINK_DATA, d => d.index);

    links.enter().append("line")
        .attr("stroke-width", 2)
        .attr("visibility", "hidden")
        .interrupt("foo")
        .transition("foo").delay(280).duration(0)
            .attr("visibility", "");

    links.exit().remove();

    let nodes = G_NODE.selectAll("rect").data(NODE_DATA, d => d.id);

    let new_nodes = nodes.enter().append("rect");

    nodes.merge(new_nodes)
        .attr("width", function(d) {let width = d3.select(this).attr("width"); return width ? width : 0;})
        .attr("height", function(d) {let height = d3.select(this).attr("height"); return height ? height : 0;})
        .transition("nodes").duration(280)
            .attr("width", RADIUS * 2)
            .attr("height", RADIUS * 2);

    new_nodes
        .attr("rx", d => GRAPH.data[d.id].is_archive ? RADIUS * 0.4 : RADIUS)
        .attr("ry", d => GRAPH.data[d.id].is_archive ? RADIUS * 0.4 : RADIUS)
        .call(d3.drag()
          .on("start", dragstarted)
          .on("drag", dragged)
          .on("end", dragended))
        .on("click", on_click_node)
        .on("mouseover", on_mouseover_node)
        .on("mouseout", on_mouseout_node)
        .append("title")
          .text(d => d.id);

    nodes.exit()
        .transition("nodes")
            .delay(0)
            .duration(100)
            .attr("width", 0)
            .attr("height", 0)
            .remove();

    let group_selected = undefined;
    GRAPH.nodes.forEach(node => group_selected = node.is_group_selected ? node.group : group_selected);

    nodes.merge(new_nodes)
        .style("fill", d => {
            if (d.is_node_in_background) {
                return "grey";
            }
            if (group_selected === undefined || group_selected === d.group) {
                return COLOR(d.group)
            }
            return "grey";
        })
        .attr("stroke", function(d) {
            if (d.is_node_focused || d.is_node_in_splotlight || d.is_node_selected)
                return "black";
            else if (d.is_group_focused)
                return d3.select(this).style("fill");
            else
                return "none";
        })
        .attr("stroke-width", d => d.is_node_selected || d.is_node_focused || d.is_group_focused || d.is_node_in_splotlight ? "5px" : "");

    let all_links = G_LINK.selectAll("line");
    let all_nodes = G_NODE.selectAll("rect");

    // don't swap simulation.nodes and simulation.force
    SIMULATION
        .nodes(NODE_DATA)
        .on("tick", () => ticked(all_links, all_nodes));

    // scale the distance (inverse of similarity) to 10 to 50
    let min_score = Math.min.apply(null, GRAPH.links.map(link => link.value));
    let max_score = 10;
    let delta_score = max_score - min_score;

    SIMULATION.force("link")
        .links(LINK_DATA)
        .distance(d => 50 - (d.value - min_score) / delta_score * 40);
}


function jiggle(alpha=0.3, duration=300) {
    SIMULATION.alphaTarget(alpha).restart();
    setTimeout(() => SIMULATION.alphaTarget(0).restart(), duration);
}


document.addEventListener("DOMContentLoaded", event => {
    window.addEventListener("resize", on_resize);

    init_data();
    init_index();
    init_graph();
    if (HORRIBLE_TWO_NODE_HACK) cutoff(0);
    jiggle();
});
