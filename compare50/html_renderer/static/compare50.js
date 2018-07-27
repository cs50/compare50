var span_to_group = null;
var fragment_to_spans = null;

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

  // Create highlighters
  let frag_to_highlighter = {};
  for (let i = 0; i < frags.length; i++) {
    let frag = frags[i];
    frag_to_highlighter[frag.id] = () => {
      // Keep track of bgs
      let originalBackgrounds = [];

      // Find every element who's background we need to change
      let contents = frag.querySelectorAll(".highlight");

      // Set new background
      for (let j = 0; j < contents.length; j++) {
        originalBackgrounds.push(contents[j].style.backgroundColor);
        contents[j].style.backgroundColor = "#A9A9A9";
      }

      // Remember how to unset
      return () => {
        for (let j = 0; j < contents.length; j++) {
          contents[j].style.backgroundColor = originalBackgrounds[j];
        }
      }
    }
  }

  // Keep track of how to unhighlight
  let unhighlighters = [];

  // Register listener for every frag
  for (let i = 0; i < frags.length; i++) {
    let frag = frags[i];
    frag.addEventListener("mouseover", (event) => {
      // Get all fragments grouped with frag
      let grouped_fragments = get_grouped_fragments(frag.id);

      // Fragment is not part of a match, return
      if (grouped_fragments.length === 0) {
          return;
      }

      // If anything was previously highlighted, unhighlight
      if (unhighlighters.length > 0) {
        unhighlighters.forEach(unhighlight => unhighlight());
        unhighlighters = [];
      }

      // Highlight, and remember how to unhighlight
      grouped_fragments.forEach(f => unhighlighters.push(frag_to_highlighter[f]()));
    }, false);
  }
}

function get_grouped_fragments(fragment) {
  if (fragment_to_spans[fragment] === undefined) {
    return [];
  }

  // Get closest enclosing span
  let span = fragment_to_spans[fragment][0];

  // Get all fragments that need to be highlighted
  let group = span_to_group[span];
  let spans = group_to_spans[group];
  let grouped_frags = [];
  spans.forEach(s => span_to_fragments[s].forEach(f => grouped_frags.push(f)));
  return grouped_frags;
}

document.addEventListener("DOMContentLoaded", function(event) {
  init_maps();
  console.log("group_to_spans", group_to_spans);
  console.log("span_to_fragments", span_to_fragments);
  console.log("span_to_group", span_to_group);
  console.log("fragment_to_spans", fragment_to_spans);

  add_mouse_over_listeners();
});
