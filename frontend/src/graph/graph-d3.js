var d3 = require("d3");
var slider = require("d3-simple-slider");

const MIN_HEIGHT = 200;
const MIN_WIDTH = 100;
const SLIDER_HEIGHT = 100;

// Helper functions
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

function get_real_width(elem, props) {
    // if we're given a static width, use it
    if (props.width !== undefined) {
        return Math.max(props.width, MIN_WIDTH);
    }

    // calculate width of provided (likely, parent) element
    let style = getComputedStyle(elem);
    return Math.max(elem.clientWidth - parseFloat(style.paddingLeft) - parseFloat(style.paddingRight), MIN_WIDTH);
}

function get_real_height(elem, props) {
    // if we're given a static height, use it
    if (props.height !== undefined) {
        return Math.max(props.height, MIN_HEIGHT);
    }

    // calculate height of provided (likely, parent) element
    return Math.max(elem.offsetHeight - (props.slider ? SLIDER_HEIGHT : 0) - 4, MIN_HEIGHT);
}


// Graph -- store in an object to maintain state
class D3Graph {
    constructor() {
        this.SVG = null;
        this.SLIDER = null;
        this.G_NODE = null;
        this.G_LINK = null;
        this.NODE_DATA = null;
        this.LINK_DATA = null;
        this.COLOR = null;
        this.DRAG_TARGET = null;
        this.SIMULATION = null;

        this.INITIALIZED = false;

        // width & height of graph in pixels
        this.width = 0;
        this.height = 0;

        // When there are exactly two nodes in the graph, d3 sets all kinds of things to
        // NaN for an unknown reason
        // This bool exists to mark all the places in the code where we implement the hack to fix this issue.
        this.HORRIBLE_TWO_NODE_HACK = true;
    }


    // Initialize the data
    init_data(el, props, state) {
        if (this.HORRIBLE_TWO_NODE_HACK) {
            /// When there are exactly two nodes, add an additional one with an id of "" and an edge with value -1
            if (state.graph.nodes.length === 2) {
                state.graph.nodes.push({id: ""});
                state.graph.links.push({source: state.graph.nodes[0], target: "", value: -1});
                state.graph.data[""] = {is_archive: false};
            }
        }

        this.NODE_DATA = state.graph.nodes;
        this.LINK_DATA = state.graph.links;

        // simulation
        this.SIMULATION = d3.forceSimulation()
            .force("link", d3.forceLink().id(d => d.id))
            .force("charge", d3.forceManyBody().strength(-200).distanceMax(50).distanceMin(10))
            .force("collision", d3.forceCollide().radius(d => props.radius * 2));

        this.SIMULATION
            .nodes(this.NODE_DATA);

        this.SIMULATION.force("link")
            .links(this.LINK_DATA);

        // assign groups to nodes
        let group_map = get_group_map(state.graph.links.map(d => ({source: d.source.id, target: d.target.id})));
        state.graph.nodes.forEach(d => d.group = group_map[d.id]);

        if (this.COLOR === null) {
            // set COLOR (function from group => color)
            let n_groups = Math.max.apply(0, state.graph.nodes.map(node => node.group));
            this.COLOR = d3.scaleSequential().domain([0, n_groups + 1]).interpolator(d3.interpolateRainbow);
        }
    }

    // Initialize the graph visualization
    init_graph(el, props, state) {
        this.SVG = d3.select(el);

        // If svg is clicked, unselect node
        this.SVG.on("click", () => {
            state.graph.nodes.forEach(node =>
                node.is_node_in_spotlight = node.is_node_in_background = node.is_node_focused = node.is_group_focused = node.is_group_selected = node.is_node_selected = false)

            props.callbacks.deselect();
            this.update(el, props, state);
        });

        // Slider
        if (props.slider) {
            let slider_start = null;
            if (this.HORRIBLE_TWO_NODE_HACK) {
                // Because the hack adds an edge with weight -1, filter it out
                slider_start = Math.floor(Math.min(...this.LINK_DATA.map(d => d.value).filter(v => v >= 0)));
            } else {
                slider_start = Math.floor(Math.min(...this.LINK_DATA.map(d => d.value)))
            }

            this.SLIDER = slider
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
                .on("onchange", (event) => { this.cutoff(event, el, props, state) })
                .handle(
                    d3
                    .symbol()
                    .type(d3.symbolCircle)
                    .size(200)()
                );

            this.SLIDER_EL
                .append("svg")
                    .attr("height", SLIDER_HEIGHT)
                .append("g")
                    .attr("transform", "translate(30,30)");
        }

        this.G_LINK = this.SVG.append("g").attr("class", "links");
        this.G_NODE = this.SVG.append("g").attr("class", "nodes");

        // scale graph and slider
        this.on_resize(el, props, state);

        // add data to graph
        this.update(el, props, state);

        let choseX = d3.randomUniform(this.width / 4, 3 * this.width / 4);
        let choseY = d3.randomUniform(this.height / 4, 3 * this.height / 4);
        let pos_map = []
        this.NODE_DATA.forEach(d => {
            if (pos_map[d.group] === undefined) {
                pos_map[d.group] = {
                    x: choseX(),
                    y: choseY()
                };
            }
        });

        this.SIMULATION.force("x", d3.forceX(d => pos_map[d.group].x).strength(0.2))
                .force("y", d3.forceY(d => pos_map[d.group].y).strength(0.2));

        setTimeout(() => this.SIMULATION.force("x", null).force("y", null), 300);
    }

    cutoff(n, el, props, state) {
        this.LINK_DATA = state.graph.links.filter(d => (d.value) >= n);
        let node_ids = new Set(this.LINK_DATA.map(d => d.source.id).concat(this.LINK_DATA.map(d => d.target.id)));
        this.NODE_DATA = state.graph.nodes.filter(d => node_ids.has(d.id));

        this.update(el, props, state);

        this.jiggle(.1);
    }

    jiggle(alpha=0.3, duration=300) {
        this.SIMULATION.alphaTarget(alpha).restart();
        setTimeout(() => this.SIMULATION.alphaTarget(0).restart(), duration);
    }

    ticked(links, nodes, el, props) {
        nodes
            .attr("x", function(d) { return d.x = Math.max(props.radius, Math.min(get_real_width(el.parentNode, props) - props.radius * 3, d.x)); })
            .attr("y", function(d) { return d.y = Math.max(props.radius, Math.min(get_real_height(el.parentNode, props) - props.radius * 3, d.y)); });

        links
            .attr("x1", function(d) { return d.source.x + props.radius; })
            .attr("y1", function(d) { return d.source.y + props.radius; })
            .attr("x2", function(d) { return d.target.x + props.radius; })
            .attr("y2", function(d) { return d.target.y + props.radius; });
    }

    dragstarted(d, el, props, state) {
        if (!d3.event.active) this.SIMULATION.alphaTarget(0.15).restart();
        d.fx = d.x;
        d.fy = d.y;

        this.DRAG_TARGET = d;
    }

    dragged(d) {
        d.fx = d3.event.x;
        d.fy = d3.event.y;
    }

    dragended(d, el, props, state) {
        if (!d3.event.active) this.SIMULATION.alphaTarget(0);
        d.fx = null;
        d.fy = null;

        let drag_target = this.DRAG_TARGET;
        this.DRAG_TARGET = null;

        this.on_mouseout_node(drag_target, el, props, state);
    }

    on_mouseover_node(d, el, props, state) {
        if (this.DRAG_TARGET !== null) {
          return;
        }

        state.graph.nodes.forEach(node => {
            node.is_group_focused = node.group === d.group;
            node.is_node_focused = node.id === d.id;
        });

        props.callbacks.mouseenter(d);

        this.update(el, props, state);
    }

    on_mouseout_node(d, el, props, state) {
        if (this.DRAG_TARGET !== null) {
            return;
        }

        state.graph.nodes.forEach(node => {
            node.is_group_focused = node.is_node_focused = false;
        });

        props.callbacks.mouseleave(d);

        this.update(el, props, state);
    }

    on_click_node(d, el, props, state) {
        state.graph.nodes.forEach(node => {
            node.is_node_selected = node.is_node_focused = node.id === d.id;
            node.is_group_selected = node.is_group_focused = node.group === d.group;
        });

        this.update(el, props, state);

        props.callbacks.select(d);

        d3.event.stopPropagation();
    }

    on_resize(el, props, state) {
        // if SVG hasn't loaded yet, do nothing
        if (!this.SVG) {
            return;
        }

        const width = get_real_width(el.parentNode, props);
        const height = get_real_height(el.parentNode, props);

        // if width and height didn't change, do nothing
        if (this.width === width && this.height === height) {
            return;
        }

        this.width = width;
        this.height = height;

        // resize slider iff it's loaded
        if (props.slider) {
            this.SLIDER.width(Math.floor(0.8 * this.width) - 60);

            this.SLIDER_EL
            .style("width", this.width + "px")
            .select("svg")
                .attr("width", Math.floor(0.8 * this.width))
                .select("g")
                .call(this.SLIDER);
        }

        this.SVG.attr("width", this.width).attr("height", this.height);

        this.jiggle();
    }

    create(el, slider_el, props, state) {
        if (props.color !== null) this.COLOR = props.color;

        this.init_data(el, props, state);
        this.SLIDER_EL = d3.select(slider_el);

        // Most problems with the split.js layout can be resolved by waiting a bit
        setTimeout(() => {
            this.init_graph(el, props, state);
            this.INITIALIZED = true;
            if (this.HORRIBLE_TWO_NODE_HACK) this.cutoff(0, el, props, state);
            this.jiggle();
            this.on_resize(el, props, state);

            props.callbacks.loaded();
        }, 66);
    }

    update(el, props, state) {
        if (!this.INITIALIZED) return false;

        let links = this.G_LINK.selectAll("line").data(this.LINK_DATA, d => d.index);
        links.enter().append("line")
            .attr("stroke-width", 2)
            .attr("visibility", "hidden")
            .interrupt("foo")
            .transition("foo").delay(280).duration(0)
                .attr("visibility", "");

        links.exit().remove();

        let nodes = this.G_NODE.selectAll("rect").data(this.NODE_DATA, d => d.id);
        let new_nodes = nodes.enter().append("rect");

        nodes.merge(new_nodes)
            .attr("width", function(d) {let width = d3.select(this).attr("width"); return width ? width : 0;})
            .attr("height", function(d) {let height = d3.select(this).attr("height"); return height ? height : 0;})
            .transition("nodes").duration(280)
                .attr("width", props.radius * 2)
                .attr("height", props.radius * 2);

        new_nodes
            .attr("rx", d => state.graph.data[d.id].is_archive ? props.radius * 0.4 : props.radius)
            .attr("ry", d => state.graph.data[d.id].is_archive ? props.radius * 0.4 : props.radius)
            .call(d3.drag()
              .on("start", (event) => {this.dragstarted(event, el, props, state)})
              .on("drag", this.dragged)
              .on("end", (event) => {this.dragended(event, el, props, state)}))
            .on("click", (event) => {this.on_click_node(event, el, props, state)})
            .on("mouseover", (event) => {
                this.on_mouseover_node(event, el, props, state)
            })
            .on("mouseout", (event) => {
                this.on_mouseout_node(event, el, props, state)
            })
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
        let selected_nodes = [];

        if (state.highlight !== null && state.highlight !== undefined) {
            group_selected = state.highlight.group;
            selected_nodes = state.highlight.nodes;
        }

        state.graph.nodes.forEach(node => group_selected = node.is_group_selected ? node.group : group_selected);

        nodes.merge(new_nodes)
            .style("fill", d => {
                if (d.is_node_in_background) {
                    return "grey";
                }
                if (group_selected === undefined || group_selected === d.group) {
                    return this.COLOR(d.group)
                }
                return "grey";
            })
            .attr("stroke", function(d) {
                if (d.is_node_focused || d.is_node_in_splotlight || d.is_node_selected || selected_nodes.includes(d))
                    return "black";
                else if (d.is_group_focused)
                    return d3.select(this).style("fill");
                else
                    return "none";
            })
            .attr("stroke-width", d => d.is_node_selected || d.is_node_focused || d.is_group_focused || d.is_node_in_splotlight || selected_nodes.includes(d) ? "5px" : "");

        let all_links = this.G_LINK.selectAll("line");
        let all_nodes = this.G_NODE.selectAll("rect");

        // don't swap simulation.nodes and simulation.force
        this.SIMULATION
            .nodes(this.NODE_DATA)
            .on("tick", () => this.ticked(all_links, all_nodes, el, props));

        // scale the distance (inverse of similarity) to 10 to 50
        let min_score = Math.min.apply(null, state.graph.links.map(link => link.value));
        let max_score = 10;
        let delta_score = max_score - min_score;

        this.SIMULATION.force("link")
            .links(this.LINK_DATA)
            .distance(d => 50 - (d.value - min_score) / delta_score * 40);
    }

    destroy(el, props, state) {
        d3.select(el).remove();
    }
}

export default {
    D3Graph: D3Graph,
    get_group_map: get_group_map
};
