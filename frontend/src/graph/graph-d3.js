var d3 = require("d3");
var slider = require("d3-simple-slider");

const MIN_HEIGHT = 200;
const MIN_WIDTH = 100;
const SLIDER_HEIGHT = 100;

// Graph -- store in an object to maintain state
class D3Graph {
    constructor(domElement, props) {
        this.domElement = domElement;

        /* all properties for this graph
        {
            radius: radius of each node in pixels (int)
            width: width of the graph in pixels (int)
            height: height of the graph in pixels (int)
            color: function mapping a node to a color (node => color)
            callbacks: {
                deselect: a node is deselected (node => null)
                loaded: the graph is loaded (event => null)
                mouseenter: mouse enters a node (node => null)
                mouseleave: mouse leaves a node (node => null)
                select: a node is selected (node => null) 
            }
        }
        */
        this.props = props;

        // SVG and 2 contained g elements for nodes and links respectively
        this.svg = null;
        this.gNode = null;
        this.gLink = null;

        // a D3Slider if added
        this.slider = null;

        // nodes and links in the simulation, as orignally "loaded"
        this.allNodes = null;
        this.allLinks = null;

        // just the nodes and links that are currently in view, part of the simulation
        this.nodesInView = null;
        this.linksInView = null;
        
        this.COLOR = this.props.color;

        // the node that is currently being dragged by the user
        this.dragTarget = null;
        
        // the d3 simulation (force-graph)
        this.simulation = null;

        // flag to check whether `load()` has completed
        this.hasLoaded = false;

        // width & height of graph in pixels
        this.width = 0;
        this.height = 0;

        // When there are exactly two nodes in the graph, d3 sets all kinds of things to
        // NaN for an unknown reason
        // This bool exists to mark all the places in the code where we implement the hack to fix this issue.
        this.HORRIBLE_TWO_NODE_HACK = true;

        this.graph = null;
    }

    load(graph) {
        // Can only load once, return
        if (this.hasLoaded) return;

        this.graph = graph;

        // create a shallow copy of the nodes and links, as this simulation can modify the array
        // specifically this.HORRIBLE_TWO_NODE_HACK adds an additional node
        this.allNodes = [...this.graph.nodes];
        this.allLinks = [...this.graph.links];

        this._init_data();

        // Most problems with the split.js layout can be resolved by waiting a bit
        setTimeout(() => {
            // Create slider
            if (this.slider) {
                let start = null;
                if (this.HORRIBLE_TWO_NODE_HACK) {
                    // Because the hack adds an edge with weight -1, filter it out
                    start = Math.floor(Math.min(...this.linksInView.map(d => d.value).filter(v => v >= 0)));
                } else {
                    start = Math.floor(Math.min(...this.linksInView.map(d => d.value)))
                }

                this.slider.load(start, this._cutoff.bind(this));
            }

            this._init_graph();
            this.hasLoaded = true;

            if (this.HORRIBLE_TWO_NODE_HACK) this._cutoff(0);
            this.setHighlight();
            this._jiggle();
            this.on_resize();

            this.props.callbacks.loaded();
        }, 66);
    }

    update() {
        if (!this.hasLoaded) return;

        let links = this.gLink.selectAll("line").data(this.linksInView, d => d.index);

        // Add any new links with a transition
        links.enter().append("line")
            .attr("stroke-width", 2)
            .attr("visibility", "hidden")
            .interrupt("foo")
            .transition("foo").delay(280).duration(0)
                .attr("visibility", "");

        // Remove and exiting links
        links.exit().remove();

        // select all nodes on screen, and bind the new data with the id as key
        let nodes = this.gNode.selectAll("rect").data(this.nodesInView, d => d.id);
        let new_nodes = nodes.enter().append("rect");

        // Have existing nodes or new nodes that are newly bound transition into view
        nodes.merge(new_nodes)
            .attr("width", function(d) {let width = d3.select(this).attr("width"); return width ? width : 0;})
            .attr("height", function(d) {let height = d3.select(this).attr("height"); return height ? height : 0;})
            .transition("nodes").duration(280)
                .attr("width", this.props.radius * 2)
                .attr("height", this.props.radius * 2);

        // Bind all necessary callbacks to newly created nodes
        new_nodes
            .attr("rx", d => this.graph.data[d.id].is_archive ? this.props.radius * 0.4 : this.props.radius)
            .attr("ry", d => this.graph.data[d.id].is_archive ? this.props.radius * 0.4 : this.props.radius)
            .call(d3.drag()
              .on("start", (event) => {this._dragstarted(event)})
              .on("drag", this._dragged)
              .on("end", (event) => {this._dragended(event)}))
            .on("click", (event) => {this._on_click_node(event)})
            .on("mouseover", (event) => {
                this._on_mouseover_node(event)
            })
            .on("mouseout", (event) => {
                this._on_mouseout_node(event)
            })
            .append("title")
              .text(d => d.id);
        
        // Remove any exiting nodes with a transition 
        nodes.exit()
            .transition("nodes")
                .delay(0)
                .duration(100)
                .attr("width", 0)
                .attr("height", 0)
                .remove();

        let all_links = this.gLink.selectAll("line");
        let all_nodes = this.gNode.selectAll("rect");

        // don't swap simulation.nodes and simulation.force
        this.simulation
            .nodes(this.nodesInView)
            .on("tick", () => this._ticked(all_links, all_nodes));

        // scale the distance (inverse of similarity) to 10 to 50
        let min_score = Math.min.apply(null, this.allLinks.map(link => link.value));
        let max_score = 10;
        let delta_score = max_score - min_score;

        this.simulation.force("link")
            .links(this.linksInView)
            .distance(d => 50 - (d.value - min_score) / delta_score * 40);
    }

    addSlider(sliderDomElement) {
        this.slider = new D3Slider(sliderDomElement);
    }

    destroy() {
        d3.select(this.domElement).remove();
    }

    setHighlight(highlight) {
        let group_selected = undefined;
        let selected_nodes = [];

        if (highlight !== null && highlight !== undefined) {
            group_selected = highlight.group;
            selected_nodes = highlight.nodes;
        }

        this.allNodes.forEach(node => group_selected = node.is_group_selected ? node.group : group_selected);

        // add strokes and fill depending on the state of the node (in_focus, in_spotlught, is_selected)
        this.svg.selectAll("rect")
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
                if (d.is_node_focused || d.is_node_in_splotlight || d.is_node_selected || selected_nodes.includes(d)) {
                    return "black";
                }
                else if (d.is_group_focused) {
                    return d3.select(this).style("fill");
                }
                return "none";
            })
            .attr("stroke-width", d => d.is_node_selected || d.is_node_focused || d.is_group_focused || d.is_node_in_splotlight || selected_nodes.includes(d) ? "5px" : "");
    }

    on_resize() {
        // if SVG hasn't loaded yet, do nothing
        if (!this.svg) {
            return;
        }

        const width = this._getWidth();
        const height = this._getHeight();

        // if width and height didn't change, do nothing
        if (this.width === width && this.height === height) {
            return;
        }

        this.width = width;
        this.height = height;

        // resize slider iff it's loaded
        if (this.slider) {
            this.slider.resize(width);
        }

        this.svg.attr("width", this.width).attr("height", this.height);

        this._jiggle();
    }

    _getWidth() {
        const el = this.domElement.parentNode;

        // if we're given a static width, use it
        if (this.props.width !== undefined) {
            return Math.max(this.props.width, MIN_WIDTH);
        }
    
        // calculate width of provided (likely, parent) element
        const style = getComputedStyle(el);
        return Math.max(el.clientWidth - parseFloat(style.paddingLeft) - parseFloat(style.paddingRight), MIN_WIDTH);
    }
    
    _getHeight() {
        const el = this.domElement.parentNode;

        // if we're given a static height, use it
        if (this.props.height !== undefined) {
            return Math.max(this.props.height, MIN_HEIGHT);
        }
    
        // calculate height of provided (likely, parent) element
        return Math.max(el.offsetHeight - (this.slider ? SLIDER_HEIGHT : 0) - 4, MIN_HEIGHT);
    }

    // Initialize the data
    _init_data() {
        if (this.HORRIBLE_TWO_NODE_HACK) {
            /// When there are exactly two nodes, add an additional one with an id of "" and an edge with value -1
            if (this.allNodes.length === 2) {
                this.allNodes.push({id: ""});
                this.allLinks.push({source: this.allNodes[0], target: "", value: -1});
                this.graph.data[""] = {is_archive: false};
            }
        }

        // start with all nodes and links in view
        this.nodesInView = this.allNodes;
        this.linksInView = this.allLinks;

        // start the simulation
        this.simulation = d3.forceSimulation()
            .force("link", d3.forceLink().id(d => d.id))
            .force("charge", d3.forceManyBody().strength(-200).distanceMax(50).distanceMin(10))
            .force("collision", d3.forceCollide().radius(d => this.props.radius * 2));

        this.simulation
            .nodes(this.nodesInView);

        this.simulation.force("link")
            .links(this.linksInView);

        // assign groups to nodes
        let group_map = get_group_map(this.allLinks.map(d => ({source: d.source.id, target: d.target.id})));
        this.allNodes.forEach(d => d.group = group_map[d.id]);

        if (this.COLOR === null) {
            // set COLOR (function from group => color)
            let n_groups = Math.max.apply(0, this.allNodes.map(node => node.group));
            this.COLOR = d3.scaleSequential().domain([0, n_groups + 1]).interpolator(d3.interpolateRainbow);
        }
    }

    // Initialize the graph visualization
    _init_graph() {
        this.svg = d3.select(this.domElement);

        // If svg is clicked, unselect node
        this.svg.on("click", () => {
            this.allNodes.forEach(node =>
                node.is_node_in_spotlight = node.is_node_in_background = node.is_node_focused = node.is_group_focused = node.is_group_selected = node.is_node_selected = false)

            this.props.callbacks.deselect();
            this.update();
        });

        this.gLink = this.svg.append("g").attr("class", "links");
        this.gNode = this.svg.append("g").attr("class", "nodes");

        // scale graph and slider
        this.on_resize();

        // add data to graph
        this.update();

        let choseX = d3.randomUniform(this.width / 4, 3 * this.width / 4);
        let choseY = d3.randomUniform(this.height / 4, 3 * this.height / 4);
        let pos_map = []
        this.nodesInView.forEach(d => {
            if (pos_map[d.group] === undefined) {
                pos_map[d.group] = {
                    x: choseX(),
                    y: choseY()
                };
            }
        });

        this.simulation.force("x", d3.forceX(d => pos_map[d.group].x).strength(0.2))
                .force("y", d3.forceY(d => pos_map[d.group].y).strength(0.2));

        setTimeout(() => this.simulation.force("x", null).force("y", null), 300);
    }

    _cutoff(n) {
        this.linksInView = this.allLinks.filter(d => (d.value) >= n);
        let node_ids = new Set(this.linksInView.map(d => d.source.id).concat(this.linksInView.map(d => d.target.id)));
        this.nodesInView = this.allNodes.filter(d => node_ids.has(d.id));

        this.update();

        this._jiggle(.1);
    }

    _jiggle(alpha=0.3, duration=300) {
        this.simulation.alphaTarget(alpha).restart();
        setTimeout(() => this.simulation.alphaTarget(0).restart(), duration);
    }

    _ticked(links, nodes) {
        let props = this.props;
        const width = this._getWidth();
        const height = this._getHeight();

        nodes
            .attr("x", function(d) { return d.x = Math.max(props.radius, Math.min(width - props.radius * 3, d.x)); })
            .attr("y", function(d) { return d.y = Math.max(props.radius, Math.min(height - props.radius * 3, d.y)); });

        links
            .attr("x1", function(d) { return d.source.x + props.radius; })
            .attr("y1", function(d) { return d.source.y + props.radius; })
            .attr("x2", function(d) { return d.target.x + props.radius; })
            .attr("y2", function(d) { return d.target.y + props.radius; });
    }

    _dragstarted(d) {
        if (!d3.event.active) this.simulation.alphaTarget(0.15).restart();
        d.fx = d.x;
        d.fy = d.y;

        this.dragTarget = d;
    }

    _dragged(d) {
        d.fx = d3.event.x;
        d.fy = d3.event.y;
    }

    _dragended(d) {
        if (!d3.event.active) this.simulation.alphaTarget(0);
        d.fx = null;
        d.fy = null;

        let dragTarget = this.dragTarget;
        this.dragTarget = null;

        this._on_mouseout_node(dragTarget);
    }

    _on_mouseover_node(d) {
        if (this.dragTarget !== null) {
          return;
        }

        this.allNodes.forEach(node => {
            node.is_group_focused = node.group === d.group;
            node.is_node_focused = node.id === d.id;
        });

        this.props.callbacks.mouseenter(d);

        this.update();
    }

    _on_mouseout_node(d) {
        if (this.dragTarget !== null) {
            return;
        }

        this.allNodes.forEach(node => {
            node.is_group_focused = node.is_node_focused = false;
        });

        this.props.callbacks.mouseleave(d);

        this.update();
    }

    _on_click_node(d) {
        this.allNodes.forEach(node => {
            node.is_node_selected = node.is_node_focused = node.id === d.id;
            node.is_group_selected = node.is_group_focused = node.group === d.group;
        });

        this.update();

        this.props.callbacks.select(d);

        d3.event.stopPropagation();
    }
}


class D3Slider {
    constructor(domElement) {
        this.domElement = domElement
        this.d3Element = d3.select(this.domElement);
    }

    load(start, callback) {
        this.callback = callback;

        this.d3Slider = slider
            .sliderBottom()
            .min(start)
            .max(10)
            .tickFormat(d => {
                let num = d3.format(".1f")(d)
                let [whole, fraction] = num.split(".");
                return fraction === "0" ? whole : num;
            })
            .ticks(10 - start + 1)
            .default(0)
            .fill("#2196f3")
            .on("onchange", this.callback)
            .handle(
                d3
                .symbol()
                .type(d3.symbolCircle)
                .size(200)()
            );
        
        this.d3Element
            .append("svg")
                .attr("height", SLIDER_HEIGHT)
            .append("g")
                .attr("transform", "translate(30,30)");
    }

    resize(width) {
        this.d3Slider.width(Math.floor(0.8 * width) - 60);
        
        this.d3Element
            .style("width", width + "px")
            .select("svg")
                .attr("width", Math.floor(0.8 * width))
                .select("g")
                .call(this.d3Slider);
    }
}

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


export default {
    D3Graph: D3Graph,
    get_group_map: get_group_map
};
