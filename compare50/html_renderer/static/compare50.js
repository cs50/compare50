class Group {
  constructor(id) {
    this.id = id;
    this.spans = [];
  }

  init(fragments, spans, groups) {
    this.spans = [];
    let obj = this;
    GROUP_TO_SPANS[this.id].forEach(span => obj.spans.push(spans[span]));
  }
}

class Span {
  constructor(id) {
    this.id = id;
    this.fragments = [];
    this.group = null;
  }

  init(fragments, spans, groups) {
    this.fragments = [];
    let obj = this;
    SPAN_TO_FRAGMENTS[this.id].forEach(frag_id => obj.fragments.push(fragments[frag_id]));
    this.group = groups[SPAN_TO_GROUP[this.id]];
  }
}

class Fragment {
  constructor(id) {
    this.id = id;
    this.dom_element = document.getElementById(id);
    this.matching_fragments = [];
    this.span = null;
    this.group = null;
    this.spans = [];
    return this;
  }

  init(fragments, spans, groups) {
    if (!FRAGMENT_TO_SPANS[this.id]) return;

    this.spans = [];
    this.groups = [];
    for (span_id of FRAGMENT_TO_SPANS[this.id]) {
      this.spans.push(spans[span_id]);
      this.groups.push(groups[SPAN_TO_GROUP[span_id]]);
    }
  
    // Get closest enclosing span & group
    this.span = this.spans[0];
    this.group = this.groups[0];
  
    this.matching_fragments = [];
    for (span_id of GROUP_TO_SPANS[this.group.id]) {
      let fragment_ids = SPAN_TO_FRAGMENTS[span_id];
      for (let i = 0; i < fragment_ids.length; i++) {
          this.matching_fragments.push(fragments[fragment_ids[i]])
      }
    }
  }

  highlight_match() {
    for (frag of this.matching_fragments) {
      frag.dom_element.classList.add("match");
    }
  }

  unhighlight() {
    this.dom_element.classList.remove("match");
  }
}

function reverse_maps() {
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

function add_mouse_over_listeners(fragments) {
  fragments.forEach(frag => {
    frag.dom_element.addEventListener("mouseover", (event) => {
      // Fragment is not part of a group, return
      if (frag.group === null) {
          return;
      }

      for (f of fragments) {
        f.unhighlight();
      }
      frag.highlight_match();
    }, false);
  });
}

function init_objects() {
  let frags = document.getElementsByClassName("fragment");
  let fragments = {};
  let spans = {};
  let groups = {};

  for (frag of frags) {
    fragments[frag.id] = new Fragment(frag.id);
  }

  for (span_id of Object.keys(SPAN_TO_GROUP)) {
    spans[span_id] = new Span(span_id);
  }

  for (group_id of Object.keys(GROUP_TO_SPANS)) {
    groups[group_id] = new Group(group_id);
  }

  Object.values(fragments).forEach(frag => frag.init(fragments, spans, groups));
  Object.values(spans).forEach(span => span.init(fragments, spans, groups));
  Object.values(groups).forEach(group => group.init(fragments, spans, groups));

  return [fragments, spans, groups];
}


document.addEventListener("DOMContentLoaded", event => {
    reverse_maps();
    console.log("GROUP_TO_SPANS", GROUP_TO_SPANS);
    console.log("SPAN_TO_FRAGMENTS", SPAN_TO_FRAGMENTS);
    console.log("SPAN_TO_GROUP", SPAN_TO_GROUP);
    console.log("FRAGMENT_TO_SPANS", FRAGMENT_TO_SPANS);

    let [fragments, spans, groups] = init_objects().map(Object.values)
    add_mouse_over_listeners(fragments);
});
