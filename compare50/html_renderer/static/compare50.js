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
    this.fragments = SPAN_TO_FRAGMENTS[this.id].map(frag_id => fragments[frag_id]);
    this.submission = this.fragments[0].submission;
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
    this.submission = document.getElementById("left").contains(this.dom_element) ? "left" : "right";
    this.spans = [];
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
  }

  // Custom implementation/hack of element.scrollIntoView();
  // Because safari does not support smooth scrolling @ 27th July 2018
  // Feel free to replace once it does:
  //     this.dom_element.scrollIntoView({"behavior":"smooth"});
  // Credits: https://gist.github.com/andjosh/6764939
  scroll_to() {
    let findPos = obj => {
      var curtop = 0;
      if (obj.offsetParent) {
        do {
          curtop += obj.offsetTop;
        } while (obj = obj.offsetParent);
      }
      return curtop;
    }
    let easeInOutQuad = (t, b, c, d) => {
      t /= d / 2;
      if (t < 1) return c / 2 * t * t + b;
      t--;
      return -c / 2 * (t * (t - 2) - 1) + b;
    };

    let scrollable = document.getElementById(this.submission);
    let to = findPos(this.dom_element) - 200;
    let duration = 300;

    let start = scrollable.scrollTop;
    let change = to - start;
    let currentTime = 0;
    let increment = 20;

    let animateScroll = () => {
      currentTime += increment;
      let val = easeInOutQuad(currentTime, start, change, duration);
      scrollable.scrollTop = val;
      if(currentTime < duration) {
        setTimeout(animateScroll, increment);
      }
    };
    animateScroll();
  }

  highlight() {
    this.dom_element.classList.add("active_match");
  }

  unhighlight() {
    this.dom_element.classList.remove("active_match");
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
    // Find all matching spans in the other file
    let other_spans = frag.group.spans.filter(span => span.submission !== frag.submission);

    // Sort by position in document
    other_spans.sort((span_a, span_b) => {
      let res = span_a.fragments[0].dom_element.compareDocumentPosition(span_b.fragments[0].dom_element)
      return res & Node.DOCUMENT_POSITION_FOLLOWING ? -1 : 1;
    });

    // Keep track of which span we've jumped to
    let i = 0;

    // Jump to next span when clicked
    frag.dom_element.addEventListener("click", event => {
      other_spans[i].fragments[0].scroll_to();
      i = (i + 1) % other_spans.length;
    });
  });
}

function init_objects() {
  let frags = document.getElementsByClassName("fragment");
  let fragments = {};
  let spans = {};
  let groups = {};

  for (let frag of frags) {
    fragments[frag.id] = new Fragment(frag.id);
  }

  for (let span_id of Object.keys(SPAN_TO_GROUP)) {
    spans[span_id] = new Span(span_id);
  }

  for (let group_id of Object.keys(GROUP_TO_SPANS)) {
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
    add_click_listeners(fragments);
});
