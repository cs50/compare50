var RADIUS = 10;
var WIDTH = null;
var HEIGHT = null;

function init() {
    SVG = d3.select("div#cluster_graph").append("svg");

    let slider_start = Math.floor(Math.min(...GRAPH.links.map(d => 11 - d.value)))

    // Slider
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
        .force("link", d3.forceLink().id(function(d) { return d.id; }))
        .force("charge", d3.forceManyBody().strength(-200).distanceMax(50).distanceMin(10))
        .force('collision', d3.forceCollide().radius(d => RADIUS * 2));

    G_LINK = SVG.append("g").attr("class", "links");

    G_NODE = SVG.append("g").attr("class", "nodes");

    // scale graph and slider
    on_resize();

    // add data to graph
    update(GRAPH.links, GRAPH.nodes);

    // Don't move this up, this needs to be after simulation.force!!!
    set_groups(GRAPH.links, GRAPH.nodes);
    color_groups();
}

function on_resize() {
  var cluster_div = document.getElementById("cluster");
  var header_size = document.querySelector("thead").clientHeight;
  cluster_div.style.paddingTop = `${header_size}px`;

  WIDTH = getRealWidth(document.getElementById("cluster"));

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
}

function getRealWidth(elem) {
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
};

function dragstarted(d) {
    if (!d3.event.active) SIMULATION.alphaTarget(0.3).restart();
    d.fx = d.x;
    d.fy = d.y;
}

function dragged(d) {
    d.fx = d3.event.x;
    d.fy = d3.event.y;
}

function dragended(d) {
    if (!d3.event.active) SIMULATION.alphaTarget(0);
    d.fx = null;
    d.fy = null;
}

function set_groups(link_data, node_data) {
    // create a map from node_id to node
    let node_map = {};
    node_data.forEach(d => {
        d.group = null;
        node_map[d.id] = d;
    });

    // create a map from node.id to directly connected node.ids
    let link_map = {};
    link_data.forEach(d => {
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

    node_data.forEach(d => d.group = node_map[d.id].group);

    // update color selecter and number of groups
    n_groups = Math.max.apply(0, node_data.map(node => +node.group));
    color = d3.scaleSequential().domain([0, n_groups + 1]).interpolator(d3.interpolateRainbow);
}

function cutoff(n) {
    let link_data = GRAPH.links.filter(d => (11 - +d.value) >= n);
    let node_ids = new Set(link_data.map(d => d.source.id).concat(link_data.map(d => d.target.id)));
    let node_data = GRAPH.nodes.filter(d => node_ids.has(d.id));

    update(link_data, node_data);
    color_groups();
}

function update(link_data, node_data) {
    let links = G_LINK.selectAll("line").data(link_data);

    links.enter().append("line")
        .attr("stroke-width", 2);

    links.exit().remove();

    let nodes = G_NODE.selectAll("circle").data(node_data);

    nodes.enter().append("circle")
        .attr("r", RADIUS)
        .call(d3.drag()
            .on("start", dragstarted)
            .on("drag", dragged)
            .on("end", dragended))
        .on("click", (d) => console.log(d.id))
        .append("title").text(d => d.id);

    nodes.exit().remove();

    let all_links = G_LINK.selectAll("line");
    let all_nodes = G_NODE.selectAll("circle");

    // don't swap simulation.nodes and simulation.force
    SIMULATION
        .nodes(node_data)
        .on("tick", () => ticked(all_links, all_nodes));

    SIMULATION.force("link")
        .links(link_data)
        .distance(d => (+d.value) * 10);

    SIMULATION.alphaTarget(0.3).restart();
    setTimeout(() => SIMULATION.alphaTarget(0).restart(), 1000);

}

function color_groups() {
    G_NODE.selectAll("circle").style("fill", d => color(+d.group))
}

init();
window.addEventListener("resize", on_resize);
