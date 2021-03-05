import React, {useRef, useEffect} from 'react';
import '../index.css';
import './graph.css';

import D3Graph from './graph-d3';


const defaultCallbacks = {
    loaded: () => null,
    mouseenter: ({
        id = -1,
        group = -1
    }) => null,
    mouseleave: () => null,
    select: ({
        id = -1,
        group = -1
    }) => null,
    deselect: () => null,
    cutoff: (n) => null
}

const defaultGraph = {
    links: [],
    nodes: []
}

const defaultHighlighted = {
    group: -1,
    nodes: []
}

function Graph({
    graph = defaultGraph,
    highlighted = defaultHighlighted,
    selected = null,
    callbacks = defaultCallbacks,
    width = undefined,
    height = undefined,
    cutoff = 0,
    slider = false,
    sliderTip = false
}) {
    callbacks = {...defaultCallbacks, ...callbacks};

    const divRef = useRef(null);
    const graphRef = useRef(null);
    const sliderRef = useRef(null);
    const d3Graph = useRef(null);

    // once this component has mounted, create the d3graph
    useEffect(() => {
        d3Graph.current = new D3Graph.D3Graph(graphRef.current, {
            radius: 10,
            width: width,
            height: height,
            callbacks: callbacks,
            cutoff: cutoff
        });

        if (slider) {
            d3Graph.current.addSlider(sliderRef.current);
        }

        d3Graph.current.load(graph);

        const resizeListener = d3Graph.current.onResize.bind(d3Graph.current);
        window.addEventListener("resize", resizeListener);

        // once this component unmounts, remove the listener and destroy the d3graph
        return () => {
            window.removeEventListener("resize", resizeListener);
            d3Graph.current.destroy();
        }
    // This effect can only run once, deliberitely passing [] to never run it twice
    // https://reactjs.org/docs/hooks-effect.html#tip-optimizing-performance-by-skipping-effects
    // eslint-disable-next-line react-hooks/exhaustive-deps
    }, []);

    // when this component updates, update the selected and highlighted selection in the d3Graph
    useEffect(() => d3Graph.current.update(selected, highlighted));

    return (
        <div ref={divRef} style={{"width": "100%", "height":"100%"}}>
            <svg className="d3graph" ref={graphRef}></svg>
            <div className="d3slider" ref={sliderRef}>
                {sliderTip &&
                <small
                    className="tooltip-marker"
                    style={{position: "absolute", marginTop: "20px"}}
                    data-tip="Slide this to hide all matches below the selected score."
                >
                    ?
                </small>
                }
            </div>
        </div>
    )
}

export default Graph;
