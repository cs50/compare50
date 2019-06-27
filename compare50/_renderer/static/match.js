class Group {
    constructor(id) {
        this.id = id;
        this.spans = [];
    }

    init(fragments, spans, groups) {
        this.spans = GROUP_TO_SPANS[this.id].map(span_id => spans[span_id]);
    }
}

class Span {
    constructor(id) {
        this.id = id;
        this.fragments = [];
        this.group = null;
        this.submission = null;
    }

    init(fragments, spans, groups) {
        this.fragments = SPAN_TO_FRAGMENTS[this.id].map(frag_id => fragments[frag_id]).sort((
            frag_a, frag_b) => {
            let res = frag_a.dom_element.compareDocumentPosition(frag_b.dom_element)
            return res & Node.DOCUMENT_POSITION_FOLLOWING ? -1 : 1;
        });
        this.submission = this.fragments[0].submission;
        this.group = groups[SPAN_TO_GROUP[this.id]];
    }
}

class Fragment {
    constructor(id, view_name) {
        this.id = id;
        this.dom_element = document.getElementById(id);
        this.matching_fragments = [];
        this.span = null;
        this.group = null;
        let left = document.getElementById(view_name + "left");
        if (left.contains(this.dom_element)) {
            this.submission = left;
        } else {
            this.submission = document.getElementById(view_name + "right");;
        }
        this.spans = [];

        // all spans grouped with this span in the other file
        this.other_spans = [];

        return this;
    }

    init(fragments, spans, groups) {
        if (!FRAGMENT_TO_SPANS[this.id]) return;

        this.dom_element.classList.add("match");
        this.spans = FRAGMENT_TO_SPANS[this.id].map(span_id => spans[span_id]);
        this.groups = FRAGMENT_TO_SPANS[this.id].map(span_id => groups[SPAN_TO_GROUP[span_id]]);

        // Get closest enclosing span & group
        this.span = this.spans[0];
        this.group = this.groups[0];

        this.matching_fragments = [];
        for (let span_id of GROUP_TO_SPANS[this.group.id]) {
            for (let frag_id of SPAN_TO_FRAGMENTS[span_id]) {
                this.matching_fragments.push(fragments[frag_id])
            }
        }

        // Find all matching spans in the other file
        this.other_spans = this.group.spans.filter(span => span.submission !== this.submission);

        // Sort by position in document
        this.other_spans.sort((span_a, span_b) => {
            let res = span_a.fragments[0].dom_element.compareDocumentPosition(
                span_b.fragments[0].dom_element)
            return res & Node.DOCUMENT_POSITION_FOLLOWING ? -1 : 1;
        });
    }

    // align this fragment with a matching fragment in the other file
    align() {
        let title_height = document.getElementById(CURRENT_VIEW + "sub_names").clientHeight;
        let frag_offset = Math.max(this._highlight_offset(), title_height);
        let next_fragment = this.other_spans.map(span => span.fragments[0]).find(
            fragment => fragment._highlight_offset() > frag_offset);

        if (next_fragment === undefined) {
            next_fragment = this.other_spans[0].fragments[0];
        }
        next_fragment.scroll_to(frag_offset);
    }

    highlight_match() {
        for (let frag of this.matching_fragments) {
            frag.dom_element.classList.add("active_match");
        }
    }

    highlight() {
        this.dom_element.classList.add("active_match");
    }

    unhighlight() {
        this.dom_element.classList.remove("active_match");
    }

    find_pos() {
        let obj = this.dom_element;
        let curtop = 0;
        if (obj.offsetParent) {
            do {
                curtop += obj.offsetTop;
            } while (obj = obj.offsetParent);
        }
        return curtop;
    }

    _highlight_offset() {
        let self_matches = this.matching_fragments.filter(frag => frag.submission === this.submission);
        let top_fragment = this;
        while (true) {
            let test_element = top_fragment.dom_element.previousElementSibling;
            let test_fragment = self_matches.find(frag => frag.dom_element === test_element);
            if (test_fragment === undefined) {
                break;
            } else {
                top_fragment = test_fragment;
            }
        }
        return top_fragment.find_pos() - this.submission.scrollTop;
    }

    // Custom implementation/hack of element.scrollIntoView();
    // Because safari does not support smooth scrolling @ 27th July 2018
    // Feel free to replace once it does:
    //     this.dom_element.scrollIntoView({"behavior":"smooth"});
    // Also see: https://github.com/iamdustan/smoothscroll
    // Credits: https://gist.github.com/andjosh/6764939
    scroll_to(offset = 200) {
        let easeInOutQuad = (t, b, c, d) => {
            t /= d / 2;
            if (t < 1) return c / 2 * t * t + b;
            t--;
            return -c / 2 * (t * (t - 2) - 1) + b;
        };

        let scrollable = this.submission;
        let to = this.find_pos() - offset;
        let duration = 300;

        let start = scrollable.scrollTop;
        let change = to - start;
        let currentTime = 0;
        let increment = 20;

        let animateScroll = () => {
            currentTime += increment;
            let val = easeInOutQuad(currentTime, start, change, duration);
            scrollable.scrollTop = val;
            if (currentTime < duration) {
                setTimeout(animateScroll, increment);
            }
            else {
                let event = new Event("finished_scrolling");
                this.dom_element.dispatchEvent(event);
            }
        };
        animateScroll();
    }
}

function init_navigation(id) {
    let prev = document.getElementById("prev_match");
    let next = document.getElementById("next_match");
    prev.addEventListener("click", (event) => window.location.href = "match_" + (id - 1) + ".html");
    next.addEventListener("click", (event) => window.location.href = "match_" + (id + 1) + ".html");
}

function init_group_button(groups, view_name) {
    function update_group_counter() {
        document.getElementById("group_counter").innerHTML = (group_index + 1) + " / " + groups.length;
    }

    // If view changed, update group counter
    document.addEventListener("view_changed", (event) => {
        if (CURRENT_VIEW === view_name) {
            update_group_counter();
        }
    });

    // If a fragment is clicked, change group to fragments group
    document.addEventListener("fragment_clicked", (event) => {
        if (CURRENT_VIEW !== view_name) {
            return;
        }
        let group = event.detail.fragment.span.group;
        group_index = sorted_groups.indexOf(group);
        update_group_counter();
    });

    // Sort all spans that are grouped by id
    let grouped_spans = [];
    groups.forEach((group) => group.spans.forEach((span) => grouped_spans.push(span)));
    grouped_spans = grouped_spans.sort((a, b) => parseInt(a.id) < parseInt(b.id) ? -1 : 1);

    // Sort groups by spans with the lowest id
    let _groups_set = new Set([]);
    let sorted_groups = [];
    for (let span of grouped_spans) {
        if (!_groups_set.has(span.group)) {
            _groups_set.add(span.group);
            sorted_groups.push(span.group);
        }
    }

    // init group counter
    let group_index = 0;
    update_group_counter();

    function go_to_next_group(event) {
        // if view is not active (current), nothing to do here
        if (CURRENT_VIEW !== view_name) {
            return;
        }

        update_group_counter();

        // find first fragment of group
        let frag = sorted_groups[group_index].spans[0].fragments[0];

        // align matching span (in the other file) once we've finished scrolling
        function callback(event) {
            frag.align();
            frag.dom_element.removeEventListener("finished_scrolling", callback);
        }
        frag.dom_element.addEventListener("finished_scrolling", callback);

        // highlight group
        frag.dom_element.dispatchEvent(new Event("mouseover"));

        // scroll to frag
        frag.scroll_to();

        // increment index
        group_index = (group_index + 1) % sorted_groups.length;

    }
    // On click move to next group from sorted_groups
    let next_group_button = document.getElementById("next_group");
    next_group_button.addEventListener("click", go_to_next_group);
    document.addEventListener("keyup", (event) =>  {
        if (event.key === ' ') {
            event.preventDefault()
            go_to_next_group(event); 
        }
    });
}

function init_maps(datum) {
    FRAGMENT_TO_SPANS = datum.fragment_to_spans;
    SPAN_TO_GROUP = datum.span_to_group;

    GROUP_TO_SPANS = {};
    Object.keys(SPAN_TO_GROUP).forEach(span => {
        let group = SPAN_TO_GROUP[span];

        if (GROUP_TO_SPANS[group] === undefined) {
            GROUP_TO_SPANS[group] = []
        }

        GROUP_TO_SPANS[group].push(span)
    });

    SPAN_TO_FRAGMENTS = {}
    Object.keys(FRAGMENT_TO_SPANS).forEach(frag => {
        FRAGMENT_TO_SPANS[frag].forEach(span => {
            if (SPAN_TO_FRAGMENTS[span] === undefined) {
                SPAN_TO_FRAGMENTS[span] = []
            }
            SPAN_TO_FRAGMENTS[span].push(frag)
        })

        if (FRAGMENT_TO_SPANS[frag].length === 0) {
            FRAGMENT_TO_SPANS[frag] = null;
        }
    });
}

function init_objects() {
    let frags = document.getElementById(CURRENT_VIEW).getElementsByClassName("fragment");
    let fragments = {};
    let spans = {};
    let groups = {};

    for (let frag of frags) {
        fragments[frag.id] = new Fragment(frag.id, CURRENT_VIEW);
    }

    for (let span_id of Object.keys(SPAN_TO_GROUP)) {
        spans[span_id] = new Span(span_id);
    }

    for (let group_id of Object.keys(GROUP_TO_SPANS)) {
        groups[group_id] = new Group(group_id);
    }

    Object.values(groups).forEach(group => group.init(fragments, spans, groups));
    Object.values(spans).forEach(span => span.init(fragments, spans, groups));
    Object.values(fragments).forEach(frag => frag.init(fragments, spans, groups));

    return [fragments, spans, groups];
}

function add_mouse_over_listeners(fragments) {
    let highlighted_frags = [];

    fragments.filter(frag => frag.group !== null).forEach(frag => {
        frag.dom_element.addEventListener("mouseover", (event) => {
            highlighted_frags.forEach(f => f.unhighlight());
            highlighted_frags = frag.matching_fragments;
            highlighted_frags.forEach(f => f.highlight());
        }, false);

        frag.dom_element.addEventListener("mouseleave", (event) => {
            highlighted_frags.forEach(f => f.unhighlight());
            highlighted_frags = [];
        }, false);
    });
}

function add_click_listeners(fragments) {
    fragments.filter(frag => frag.group !== null).forEach(frag => {
        // Jump to next span when clicked
        frag.dom_element.addEventListener("click", event => {
            frag.align();
            let frag_event = new CustomEvent("fragment_clicked", {
                bubbles: true,
                detail: {fragment: frag}
            });
            document.dispatchEvent(frag_event);
        });
    });
}

function select_view(name) {
    if (select_view._cache === undefined) {
        select_view._cache = {};
    }

    // Find view with name
    for (var datum of DATA) {
        if (datum.name === name) {
            CURRENT_VIEW = datum.name
            document.dispatchEvent(new Event("view_changed"));
            break;
        }
    }

    // Activate new view
    let views = document.getElementsByClassName("view");

    let leftScroll = 0;
    let rightScroll = 0;
    let curView = undefined;

    for (let v of views) {
        if (v.style.display === "block") {
            // TODO: get these by id instead of assuming structure
            leftScroll = v.children[1].children[0].scrollTop;
            rightScroll = v.children[1].children[1].scrollTop
        }

        if (v.id === CURRENT_VIEW) {
            v.style.display = "block";
            curView = v;
        } else {
            v.style.display = "none";
        }
    }

    curView.children[1].children[0].scrollTop = leftScroll;
    curView.children[1].children[1].scrollTop = rightScroll;

    var newurl = window.location.protocol + "//" + window.location.host + window.location.pathname +
        (datum !== DATA[0] ? `?pass=${CURRENT_VIEW}` : "")
    window.history.replaceState({ path: newurl }, '', newurl)

    // If cached, nothing to do here, return
    if (CURRENT_VIEW in select_view._cache) {
        return;
    }

    // Add all mouselisteners
    init_maps(datum);
    let [fragments, spans, groups] = init_objects().map(Object.values);
    add_mouse_over_listeners(fragments);
    add_click_listeners(fragments);
    init_group_button(groups, CURRENT_VIEW);

    // Cache this view
    select_view._cache[CURRENT_VIEW] = true;
}


function make_split(name) {
    return Split([`#${name}left`,`#${name}right`], {
        elementStyle: function (dimension, size, gutterSize) {
            window.dispatchEvent(new Event('resize'));
            return {'flex-basis': 'calc(' + size + '% - ' + gutterSize + 'px)'}
        },
        gutterStyle: function (dimension, gutterSize) { return {'flex-basis':  gutterSize + 'px'} },
        sizes: [50, 50],
        minSize: 100,
        gutterSize: 6,
        cursor: 'col-resize'
    });
}


document.addEventListener("DOMContentLoaded", event => {
    let id = parseInt(document.getElementsByClassName("id")[0].id);

    let split_info = {
        sizes: [50, 50],
        objs: {}
    }

    let selectors = document.getElementsByClassName("view_selector");
    let selector_map = {}
    for (let selector of selectors) {
        let pass_name = selector.firstChild.nodeValue;
        split_info.objs[pass_name] = make_split(pass_name);

        selector.addEventListener("click", (event) => {
            for (let s of selectors) {
                if (s.classList.contains("active")) {
                    split_info.sizes = split_info.objs[s.firstChild.nodeValue].getSizes();
                    s.classList.remove("active");
                }

            }
            selector.classList.add("active");
            split_info.objs[selector.firstChild.nodeValue].setSizes(split_info.sizes);
            select_view(selector.id.replace("selector", ""));
        });

        selector_map[selector.id.replace("selector", "")] = selector;
    }

    let url = new URL(window.location);
    (selector_map[url.searchParams.get("pass")] || selectors[0]).click()

    init_navigation(id);
});
