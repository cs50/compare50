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
    this.submission = null;
  }

  init(fragments, spans, groups) {
    this.fragments = [];
    let obj = this;
    SPAN_TO_FRAGMENTS[this.id].forEach(frag_id => obj.fragments.push(fragments[frag_id]));
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

    this.spans = [];
    this.groups = [];
    for (let span_id of FRAGMENT_TO_SPANS[this.id]) {
      this.spans.push(spans[span_id]);
      this.groups.push(groups[SPAN_TO_GROUP[span_id]]);
    }

    // Get closest enclosing span & group
    this.span = this.spans[0];
    this.group = this.groups[0];

    this.matching_fragments = [];
    for (let span_id of GROUP_TO_SPANS[this.group.id]) {
      let fragment_ids = SPAN_TO_FRAGMENTS[span_id];
      for (let frag_id of SPAN_TO_FRAGMENTS[span_id]) {
          this.matching_fragments.push(fragments[frag_id])
      }
    }
  }

  highlight_match() {
    for (let frag of this.matching_fragments) {
      frag.dom_element.classList.add("match");
    }
  }

  unhighlight() {
    this.dom_element.classList.remove("match");
  }

  // Custom implementation/hack of element.scrollIntoView();
  // Because safari does not support smooth scrolling @ 27th July 2018
  // Feel free to replace once it does:
  //     this.dom_element.scrollIntoView({"behavior":"smooth"});
  // Credits: https://gist.github.com/andjosh/6764939
  scrollTo() {
    function findPos(obj) {
        var curtop = 0;
        if (obj.offsetParent) {
            do {
                curtop += obj.offsetTop;
            } while (obj = obj.offsetParent);
        return [curtop];
        }
    }
    function easeInOutQuad(t, b, c, d) {
      t /= d/2;
      if (t < 1) return c/2*t*t + b;
      t--;
      return -c/2 * (t*(t-2) - 1) + b;
    };

    let scrollable = document.getElementById(this.submission);
    let to = findPos(this.dom_element) - 200;
    let duration = 300;

    let start = scrollable.scrollTop;
    let change = to - start;
    let currentTime = 0;
    let increment = 20;

    var animateScroll = function(){
        currentTime += increment;
        let val = easeInOutQuad(currentTime, start, change, duration);
        scrollable.scrollTop = val;
        if(currentTime < duration) {
            setTimeout(animateScroll, increment);
        }
    };
    animateScroll();
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

      for (let f of fragments) {
        f.unhighlight();
      }
      frag.highlight_match();
    }, false);
  });
}

function add_click_listeners(fragments) {
  fragments.forEach(frag => {
    if (frag.group === null) {
      return;
    }

    // Find all frags in the other file
    let other_spans = [];
    frag.group.spans.forEach(span => {
      if (span.submission !== frag.submission) {
        other_spans.push(span);
      }
    });

    // Keep track of which fragment we've jumped to
    let i = 0;
    //Finds y value of given object

    frag.dom_element.addEventListener("click", event => {
      other_spans[i].fragments[0].scrollTo();
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
