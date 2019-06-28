var RADIUS = 10;
var WIDTH = null;
var HEIGHT = null;

var SVG = null
var SLIDER = null;
var G_NODE = null;
var G_LINK = null;

var NODE_DATA = GRAPH.nodes;
var LINK_DATA = GRAPH.links;

var FOCUSED_NODE_ID = null;
var FOCUSED_GROUP_ID = null;
var HIGHLIGHTED_GROUP = null;

var COLOR = null;

function init_graph() {
    NODE_DATA = GRAPH.nodes;
    LINK_DATA = GRAPH.links;

    SVG = d3.select("div#cluster_graph").append("svg");

    // If svg is clicked, unselect node
    SVG.on("click", () => {
        GRAPH.nodes.forEach(node => 
            node.is_node_focused = node.is_group_focused = node.is_group_selected = node.is_node_selected = false)
        update();
    });

    // Slider
    let slider_start = Math.floor(Math.min(...LINK_DATA.map(d => d.value)))

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

    // simulation
    SIMULATION = d3.forceSimulation()
        .force("link", d3.forceLink().id(d => d.id))
        .force("charge", d3.forceManyBody().strength(-200).distanceMax(50).distanceMin(10))
        .force('collision', d3.forceCollide().radius(d => RADIUS * 2));

    G_LINK = SVG.append("g").attr("class", "links");

    G_NODE = SVG.append("g").attr("class", "nodes");

    // scale graph and slider
    on_resize();

    // add data to graph
    update_graph();

    // Don't move this up, this needs to be after simulation.force!!!
    set_groups();

    set_color();

    color_groups();

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

    SIMULATION.force("center", d3.forceCenter(WIDTH / 2, HEIGHT / 2));
    jiggle();
}


function get_real_width(elem) {
    let style = getComputedStyle(elem);
    return elem.clientWidth - parseFloat(style.paddingLeft) - parseFloat(style.paddingRight);
}


function ticked(links, nodes) {
    nodes
        .attr("cx", function(d) { return d.x = Math.max(RADIUS, Math.min(WIDTH - RADIUS, d.x)); })
        .attr("cy", function(d) { return d.y = Math.max(RADIUS, Math.min(HEIGHT - RADIUS, d.y)); });

    links
        .attr("x1", function(d) { return d.source.x; })
        .attr("y1", function(d) { return d.source.y; })
        .attr("x2", function(d) { return d.target.x; })
        .attr("y2", function(d) { return d.target.y; });
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

function get_grouped_nodes(node) {
    return NODE_DATA.filter(other_node => other_node.group === node.group);
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


function set_color(f=null) {
    if (f === null) {
        let n_groups = Math.max.apply(0, NODE_DATA.map(node => +node.group));
        COLOR = d3.scaleSequential().domain([0, n_groups + 1]).interpolator(d3.interpolateRainbow);
    } else {
        COLOR = f;
    }
}

function set_groups() {
    // create a map from node_id to node
    let node_map = {};
    NODE_DATA.forEach(d => {
        d.group = null;
        node_map[d.id] = d;
    });

    // create a map from node.id to directly connected node.ids
    let link_map = {};
    LINK_DATA.forEach(d => {
        if (d.source.id in link_map) {
            link_map[d.source.id].push(d.target.id);
        } else {
            link_map[d.source.id] = [d.target.id];
        }

        if (d.target.id in link_map) {
            link_map[d.target.id].push(d.source.id);
        } else {
            link_map[d.target.id] = [d.source.id];
        }
    })

    let group_id = 0;
    let visited = new Set();
    let unseen = new Set(Object.keys(node_map));

    // visit all nodes
    while (unseen.size > 0) {
        // start with an unseen node
        let node_id = unseen.values().next().value;
        unseen.delete(node_id);

        // DFS for all reachable nodes, start with all directly reachable
        let stack = [node_id];
        while (stack.length > 0) {
            // take top node on stack
            let cur_node_id = stack.pop();

            // visit it, give it a group
            visited.add(cur_node_id);
            node_map[cur_node_id].group = group_id;

            // add all directly reachable (and unvisited nodes) to stack
            let directly_reachable = link_map[cur_node_id].filter(id => unseen.has(id));
            stack = stack.concat(directly_reachable);

            // remove all directly reachable elements from unseen
            directly_reachable.forEach(id => unseen.delete(id));
        }

        group_id++;
    }

    NODE_DATA.forEach(d => d.group = node_map[d.id].group);
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
    let table_data = INDEX.selectAll("tr").data(LINK_DATA);

    let new_trs = table_data.enter().append("tr");
    new_trs.append("th");
    for (let i = 0; i != 3; i++) {
        new_trs.append("td");
    }

    let group_selected = undefined;
    GRAPH.nodes.forEach(node => group_selected = node.is_group_selected ? node.group : group_selected);

    let all_data = table_data.merge(new_trs)
        .each(function (d) {
            let tr = d3.select(this);
            tr.select("th").attr("scope", "row").text(d => d.index + 1);

            // I HATE IT
            let tds = tr.selectAll("td");
            let source = d.source.id === undefined ? d.source : d.source.id;
            let target = d.target.id === undefined ? d.target : d.target.id;
            tds.filter((d,i) => i == 0)
                .attr("class", d => `${source}_index`)
                .text(d => source)
                .style("background-color", d => d.source.is_node_focused ? "#CCCCCC" : "")
                .style("font-family", d => d.source.is_node_selected ? "Roboto-Bold" : "");
            tds.filter((d,i) => i == 1)
                .attr("class", d => `${target}_index`)
                .text(d => target)
                .style("background-color", d => d.target.is_node_focused ? "#CCCCCC" : "")
                .style("font-family", d => d.target.is_node_selected ? "Roboto-Bold" : "");
            tds.filter((d, i) => i == 2)
                .attr("class", "score")
                .text(d => d.value.toFixed(1))
                .style("border-right", d => d.source.group === undefined ? "" : `10px solid ${COLOR(d.source.group)}`);
        })
        .style("background-color", link => {
            if (link.source.is_group_focused && !link.source.is_group_selected) {
                return "#ECECEC";
            } else {
                return "";
            }
        })
        .style("display", link => {
            if (group_selected !== undefined && group_selected !== link.source.group) {
                return "none";
            } else {
                return "";
            }
        })
        .on("mouseover", link => {
            GRAPH.nodes.forEach(node => {
                node.is_group_focused = false;
                node.is_group_selected = node.group === link.source.group;
                node.is_node_focused = node.id === link.source.id || node.id === link.target.id;
                update_graph();
            });
        })
        .on("mouseout", link => {
          GRAPH.nodes.forEach(node => {
            node.is_group_focused = false;
            node.is_node_focused = false;
         })
         update_graph();
       });

    table_data.exit().remove();
}

function update_graph() {
    let links = G_LINK.selectAll("line").data(LINK_DATA);

    links.enter().append("line")
        .attr("stroke-width", 2);

    links.exit().remove();

    let nodes = G_NODE.selectAll("circle").data(NODE_DATA);

    let new_nodes = nodes.enter().append("circle");

    new_nodes
        .attr("r", RADIUS)
        .call(d3.drag()
          .on("start", dragstarted)
          .on("drag", dragged)
          .on("end", dragended))
        .on("click", on_click_node)
        .on("mouseover", on_mouseover_node)
        .on("mouseout", on_mouseout_node)
        .append("title")
          .text(d => d.id);

    nodes.exit().remove();

    nodes.merge(new_nodes)
        .attr("stroke", function(d) {
            if (d.is_node_focused)
                return "black";
            else if (d.is_group_focused)
                return d3.select(this).style("fill");
            else
                return "none";
        })
        .attr("stroke-width", d => d.is_node_focused || d.is_group_focused ? "5px" : "");

    let all_links = G_LINK.selectAll("line");
    let all_nodes = G_NODE.selectAll("circle");

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

    if (COLOR !== null) {
        color_groups();
    }
}

function color_groups() {
    let group_selected = undefined;
    GRAPH.nodes.forEach(node => group_selected = node.is_group_selected ? node.group : group_selected);

    G_NODE.selectAll("circle").style("fill", d => group_selected === undefined || group_selected === d.group ? COLOR(d.group) : "grey");
}

function jiggle(alpha=0.3, duration=300) {
    SIMULATION.alphaTarget(alpha).restart();
    setTimeout(() => SIMULATION.alphaTarget(0).restart(), duration);
}


document.addEventListener("DOMContentLoaded", event => {
    window.addEventListener("resize", on_resize);
    init_index();
    init_graph();
    update();
    jiggle();
});
