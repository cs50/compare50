var span_to_group = null;
var fragment_to_spans = null;

function Group(id) {
  this.id = id;
  this.spans = [];
  return this;
}
Group.prototype.init = function(fragments, spans, groups) {
  this.spans = [];
  let obj = this;
  group_to_spans[this.id].forEach(span => obj.spans.push(spans[span]));
}

function Span(id) {
  this.id = id;
  this.fragments = [];
  this.group = null;
  return this;
}
Span.prototype.init = function(fragments, spans, groups) {
  this.fragments = [];
  let obj = this;
  span_to_fragments[this.id].forEach(frag_id => obj.fragments.push(fragments[frag_id]));
  this.group = groups[span_to_group[this.id]];
}

function Fragment(id) {
  this.id = id;
  this.dom_element = document.getElementById(id);
  this.fragments = [];
  this.span = null;
  this.group = null;
  this.spans = [];
  return this;
}
Fragment.prototype.init = function(fragments, spans, groups) {
  if (fragment_to_spans[this.id] !== undefined) {
    this.spans = [];
    this.groups = [];
    for (span_id of fragment_to_spans[this.id]) {
      this.spans.push(spans[span_id]);
      this.groups.push(groups[span_to_group[span_id]]);
    }

    // Get closest enclosing span & group
    this.span = this.spans[0];
    this.group = this.groups[0];

    this.fragments = [];
    for (span of this.spans) {
      for (frag_id of span_to_fragments[span.id]) {
        this.fragments.push(fragments[frag_id]);
      }
    }
  }
}


function init_maps() {
  // Create span_to_group
  span_to_group = {};
  Object.keys(group_to_spans).forEach(group => {
    let spans = group_to_spans[group];
    spans.forEach(span => span_to_group[span] = group);
  });

  // Create fragment_to_spans
  fragment_to_spans = {};
  Object.values(span_to_fragments).forEach(frags => frags.forEach(frag => fragment_to_spans[frag] = []));
  Object.keys(span_to_fragments).forEach(span => {
    let frags = span_to_fragments[span];
    frags.forEach(frag => fragment_to_spans[frag].push(span));
  });
}

function add_mouse_over_listeners() {
  let frags = document.getElementsByClassName("fragment");

  for (frag of frags) {
    let frag = frag; // I hate javascript
    frag.addEventListener("mouseover", (event) => {
      // Get all fragments grouped with frag
      let grouped_fragments = get_grouped_fragments(frag.id);

      // Fragment is not part of a match, return
      if (grouped_fragments.length === 0) {
          return;
      }
      
      for (f of frags) {
         f.classList.remove("match")
      }
      grouped_fragments.forEach(f => {
          document.getElementById(f).classList.add("match")
      })
    }, false);
  }
}

function init_objects() {
  let frags = document.getElementsByClassName("fragment");
  let fragments = {};
  let spans = {};
  let groups = {};

  for (frag of frags) {
    fragments[frag.id] = new Fragment(frag.id);
  }

  for (span_id of Object.keys(span_to_group)) {
    spans[span_id] = new Span(span_id);
  }

  for (group_id of Object.keys(group_to_spans)) {
    groups[group_id] = new Group(group_id);
  }

  console.log(fragments);
  Object.values(fragments).forEach(frag => frag.init(fragments, spans, groups));
  Object.values(spans).forEach(span => span.init(fragments, spans, groups));
  Object.values(groups).forEach(group => group.init(fragments, spans, groups));

  return [fragments, spans, groups];
}

document.addEventListener("DOMContentLoaded", function(event) {
  init_maps();
  console.log("group_to_spans", group_to_spans);
  console.log("span_to_fragments", span_to_fragments);
  console.log("span_to_group", span_to_group);
  console.log("fragment_to_spans", fragment_to_spans);

  objs = init_objects();
  console.log(objs);

  //add_mouse_over_listeners();
});
