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

        this._initData();

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

            this._initGraph();
            this.hasLoaded = true;
            this._cutoff(this.props.cutoff);
            this.setHighlighted();
            this._jiggle();
            this.onResize();

            this.props.callbacks.loaded();
        }, 66);
    }

    update() {
        if (!this.hasLoaded) return;

        const links = this.gLink.selectAll("line").data(this.linksInView, d => d.index);

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
        const nodes = this.gNode.selectAll("rect").data(this.nodesInView, d => d.id);
        const newNodes = nodes.enter().append("rect");

        // Have existing nodes or new nodes that are newly bound transition into view
        nodes.merge(newNodes)
            .attr("width", function() {
                const width = d3.select(this).attr("width");
                return width ? width : 0;
            })
            .attr("height", function() {
                const height = d3.select(this).attr("height");
                return height ? height : 0;
            })
            .transition("nodes").duration(280)
                .attr("width", this.props.radius * 2)
                .attr("height", this.props.radius * 2);

        // Bind all necessary callbacks to newly created nodes
        newNodes
            .attr("rx", d => d.isArchive ? this.props.radius * 0.4 : this.props.radius)
            .attr("ry", d => d.isArchive ? this.props.radius * 0.4 : this.props.radius)
            .call(d3.drag()
              .on("start", this._dragstarted.bind(this))
              .on("drag", this._dragged)
              .on("end", this._dragended.bind(this)))
            .on("click", this._onClickNode.bind(this))
            .on("mouseover", this._onMouseoverNode.bind(this))
            .on("mouseout", this._onMouseoutNode.bind(this))
            .append("title")
              .text(d => d.id);
        
        // style each node
        this._styleNodes(newNodes);

        // Remove any exiting nodes with a transition 
        nodes.exit()
            .transition("nodes")
                .delay(0)
                .duration(100)
                .attr("width", 0)
                .attr("height", 0)
                .remove();

        const allLinks = this.gLink.selectAll("line");
        const allNodes = this.gNode.selectAll("rect");

        // don't swap simulation.nodes and simulation.force
        this.simulation
            .nodes(this.nodesInView)
            .on("tick", () => this._ticked(allLinks, allNodes));

        // scale the distance (inverse of similarity) to 10 to 50
        const minScore = Math.min.apply(null, this.allLinks.map(link => link.value));
        const maxScore = 10;
        const deltaScore = maxScore - minScore;

        this.simulation.force("link")
            .links(this.linksInView)
            .distance(d => 50 - (d.value - minScore) / deltaScore * 40);
    }

    addSlider(sliderDomElement) {
        this.slider = new D3Slider(sliderDomElement);
    }

    destroy() {
        d3.select(this.domElement).remove();
    }

    setHighlighted(highlighted) {
        if (!this.hasLoaded) return;

        if (highlighted !== null && highlighted !== undefined) {
            this.allNodes.forEach(d => d.isHighlighted = highlighted.nodes.includes(d.id));
        }
        else {
            this.allNodes.forEach(d => d.isHighlighted = false);
        }
        
        this._styleNodes(this.svg.selectAll("rect"));
    }

    onResize() {
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
    _initData() {
        if (this.HORRIBLE_TWO_NODE_HACK) {
            /// When there are exactly two nodes, add an additional one with an id of "" and an edge with value -1
            if (this.allNodes.length === 2) {
                this.allNodes.push({id: ""});
                this.allLinks.push({source: this.allNodes[0], target: "", value: -1});
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
    }

    // Initialize the graph visualization
    _initGraph() {
        this.svg = d3.select(this.domElement);

        // If svg is clicked, unselect node
        this.svg.on("click", () => {
            this.allNodes.forEach(node =>
                node.isHighlighted = node.isSelected = false)

            this.props.callbacks.deselect();
        });

        this.gLink = this.svg.append("g").attr("class", "links");
        this.gNode = this.svg.append("g").attr("class", "nodes");

        // scale graph and slider
        this.onResize();

        let choseX = d3.randomUniform(this.width / 4, 3 * this.width / 4);
        let choseY = d3.randomUniform(this.height / 4, 3 * this.height / 4);
        let posMap = []
        this.nodesInView.forEach(d => {
            if (posMap[d.group] === undefined) {
                posMap[d.group] = {
                    x: choseX(),
                    y: choseY()
                };
            }
        });

        this.simulation.force("x", d3.forceX(d => posMap[d.group].x).strength(0.2))
                .force("y", d3.forceY(d => posMap[d.group].y).strength(0.2));

        setTimeout(() => this.simulation.force("x", null).force("y", null), 300);
    }

    _styleNodes(nodes) {
        const highlightedNode = this.allNodes.find(node => node.isHighlighted);
        const highlightedGroup = highlightedNode !== undefined ? highlightedNode.group : null;
        
        const selectedNode = this.allNodes.find(node => node.isSelected);
        const selectedGroup = selectedNode !== undefined ? selectedNode.group : null;

        // add strokes and fill depending on the state of the node (highlighted & selected)
        nodes.style("fill", d => {
            if (highlightedGroup === null && selectedGroup === null) {
                return d.color;
            }
            if (highlightedGroup !== null && highlightedGroup === d.group) {
                return d.color;
            }
            if (selectedGroup !== null && selectedGroup === d.group) {
                return d.color;
            }
            return "grey";
        })
        .attr("stroke", function(d) {
            if (d.isSelected || d.isHighlighted) {
                return "black";
            }
            if (d.group === highlightedGroup) {
                return d3.select(this).style("fill");
            }
            return "none";
        })
        .attr("stroke-width", d => d.isSelected || d.isHighlighted ? "5px" : "");
    }

    _cutoff(n) {
        this.linksInView = this.allLinks.filter(d => (d.value) >= n);
        const nodeIds = new Set(this.linksInView.map(d => d.source.id).concat(this.linksInView.map(d => d.target.id)));
        this.nodesInView = this.allNodes.filter(d => nodeIds.has(d.id));

        this.update();
        this._jiggle(.1);

        this.props.callbacks.cutoff(n);
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
        this._dragstarted.startSimulationTimeout = setTimeout(() => this.simulation.alphaTarget(0.15).restart(), 150);
    
        d.fx = d.x;
        d.fy = d.y;
    
        this.dragTarget = d;
    }
    
    _dragged(d) {
        d.fx = d3.event.x;
        d.fy = d3.event.y;
    }
    
    _dragended(d) {
        clearTimeout(this._dragstarted.startSimulationTimeout);
        this.simulation.alphaTarget(0);
        d.fx = null;
        d.fy = null;
    
        let dragTarget = this.dragTarget;
        this.dragTarget = null;
    
        this._onMouseoutNode(dragTarget);
    }

    _onMouseoverNode(d) {
        if (this.dragTarget !== null) {
          return;
        }

        this.allNodes.forEach(node => {
            node.isHighlighted = node.id === d.id;
        });

        this.props.callbacks.mouseenter(d);
    }

    _onMouseoutNode(d) {
        if (this.dragTarget !== null) {
            return;
        }

        this.props.callbacks.mouseleave(d);
    }

    _onClickNode(d) {
        this.allNodes.forEach(node => {
            node.isSelected = node.isHighlighted = node.id === d.id;
        });

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
        const roundToOneDecimal = (n) => Math.round(n * 10) / 10;

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
            .on("onchange", (n) => {
                n = roundToOneDecimal(n);

                // if slider value didnt change more than one decimal point, ignore
                if (n === currentN) {
                    return;
                }

                currentN = n;
                callback(n);
            })
            .handle(
                d3
                .symbol()
                .type(d3.symbolCircle)
                .size(200)()
            );
        
        // Keep track of current slider value
        let currentN = roundToOneDecimal(this.d3Slider.value());

        this.d3Element
            .append("svg")
                .attr("height", SLIDER_HEIGHT)
            .append("g")
                .attr("transform", "translate(30,30)");
    }

    resize(width) {
        this.d3Slider.width(Math.floor(0.9 * width) - 60);
        
        this.d3Element
            .style("width", width + "px")
            .select("svg")
                .attr("width", Math.floor(0.9 * width))
                .select("g")
                .call(this.d3Slider);
    }
}


export default {
    D3Graph: D3Graph
};
